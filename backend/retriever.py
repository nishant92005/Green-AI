"""Retrieval layer: multi-query + HyDE, child search, parent mapping, deduplication."""

import time
from typing import List, Tuple

import numpy as np

from .config import TOP_K_CHILDREN
from .embeddings import embed_batch
from .vector_store import search, get_children_by_indices, get_all_children, child_count
from .document_store import get_parents_by_ids
from .query_processing import expand_queries, generate_hyde


def _collect_child_indices_from_search_results(
    search_results: List[List[tuple]],
) -> List[int]:
    """Flatten (child_idx, dist) from all query results and deduplicate by child index."""
    seen = set()
    order = []
    for query_hits in search_results:
        for idx, _ in query_hits:
            if idx not in seen:
                seen.add(idx)
                order.append(idx)
    return order


def retrieve(
    query: str,
    top_k: int = None,
    use_multi_query: bool = True,
    use_hyde: bool = True,
) -> Tuple[List[str], List[dict], float]:
    """
    Run full retrieval: expand query, HyDE, embed all, search children, map to parents, dedupe.
    Returns (context_strings, source_metadata_list, retrieval_time_seconds).
    """
    t0 = time.perf_counter()
    k = top_k or TOP_K_CHILDREN

    # Build texts to embed: original + expanded + HyDE
    texts_to_embed = [query]
    if use_multi_query:
        expanded = expand_queries(query)
        texts_to_embed.extend(expanded[:5])  # cap at 5
    if use_hyde:
        hyde_text = generate_hyde(query)
        texts_to_embed.append(hyde_text)

    # Dedupe while preserving order
    seen = set()
    unique_texts = []
    for t in texts_to_embed:
        if t and t not in seen:
            seen.add(t)
            unique_texts.append(t)

    if not unique_texts:
        return [], [], time.perf_counter() - t0

    # Embed and search
    vectors = embed_batch(unique_texts)
    if vectors.size == 0:
        return [], [], time.perf_counter() - t0

    n_children = child_count()
    if n_children == 0:
        return [], [], time.perf_counter() - t0

    search_results = search(vectors, min(k, n_children))
    child_indices = _collect_child_indices_from_search_results(search_results)

    # Map to parent IDs and deduplicate parents
    children = get_children_by_indices(child_indices)
    parent_ids_ordered = []
    seen_parents = set()
    for c in children:
        pid = c.get("parent_id")
        if pid and pid not in seen_parents:
            seen_parents.add(pid)
            parent_ids_ordered.append(pid)

    parents = get_parents_by_ids(parent_ids_ordered)
    context_strings = [p.get("content", "") for p in parents if p.get("content")]
    sources = [{"parent_id": p.get("parent_id"), "source": p.get("source", ""), "metadata": p.get("metadata", {})} for p in parents]

    elapsed = time.perf_counter() - t0
    return context_strings, sources, elapsed
