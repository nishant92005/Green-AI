"""Vector store for child chunks (FAISS + in-memory child list)."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import faiss

from .config import DATA_DIR, VECTOR_INDEX_PATH, EMBEDDING_DIM
from .embeddings import embed_batch, get_embedding_dim


_CHILDREN: List[Dict[str, Any]] = []
_INDEX: Optional[faiss.IndexFlatIP] = None
_DIM = get_embedding_dim()



def _ensure_index():
    global _INDEX
    if _INDEX is None:
        # Use inner product on L2-normalized vectors → cosine similarity
        _INDEX = faiss.IndexFlatIP(_DIM)


def add_children(children: List[Dict[str, Any]], vectors: np.ndarray) -> None:
    """Add child chunks and their vectors."""
    global _CHILDREN, _INDEX
    _ensure_index()
    vectors = np.asarray(vectors, dtype=np.float32)
    if vectors.shape[0] != len(children) or vectors.shape[1] != _DIM:
        raise ValueError("vectors shape must be (len(children), embedding_dim)")
    # Normalize so inner product approximates cosine similarity
    faiss.normalize_L2(vectors)
    _INDEX.add(vectors)
    _CHILDREN.extend(children)


def search(query_vectors: np.ndarray, top_k: int) -> List[List[tuple]]:
    """
    query_vectors: (n_queries, dim).
    Returns list of length n_queries; each element is list of (child_idx, distance).
    """
    _ensure_index()
    n = _INDEX.ntotal
    if n == 0:
        return [[] for _ in range(len(query_vectors))]
    k = min(top_k, n)
    query_vectors = np.asarray(query_vectors, dtype=np.float32)
    # Normalize queries as well for cosine similarity
    faiss.normalize_L2(query_vectors)
    distances, indices = _INDEX.search(query_vectors, k)
    results = []
    for i in range(len(query_vectors)):
        results.append(list(zip(indices[i].tolist(), distances[i].tolist())))
    return results


def get_children_by_indices(indices: List[int]) -> List[Dict[str, Any]]:
    """Return child dicts by index in _CHILDREN."""
    return [_CHILDREN[i] for i in indices if 0 <= i < len(_CHILDREN)]


def get_all_children() -> List[Dict[str, Any]]:
    return list(_CHILDREN)


def child_count() -> int:
    return len(_CHILDREN)


def save_to_disk() -> None:
    """Persist index and children to DATA_DIR."""
    _ensure_index()
    path_idx = Path(VECTOR_INDEX_PATH)
    path_idx.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(_INDEX, str(path_idx))
    path_children = path_idx.parent / "children.json"
    with open(path_children, "w", encoding="utf-8") as f:
        json.dump(_CHILDREN, f, indent=2, ensure_ascii=False)


def load_from_disk() -> bool:
    """Load index and children from disk. Returns True if loaded."""
    global _CHILDREN, _INDEX
    path_idx = Path(VECTOR_INDEX_PATH)
    path_children = path_idx.parent / "children.json"
    if not path_idx.exists() or not path_children.exists():
        return False
    _INDEX = faiss.read_index(str(path_idx))
    with open(path_children, "r", encoding="utf-8") as f:
        _CHILDREN = json.load(f)
    return True
