"""Intelligent Parent-Child chunking for RAG.

- Parent chunks: large semantic sections (document store).
- Child chunks: small embedding units (vector DB).
- Maintains child_id -> parent_id mapping.
"""

import re
import uuid
from typing import List, Tuple
from dataclasses import dataclass, asdict


@dataclass
class ParentChunk:
    """Large semantic section for document store."""
    parent_id: str
    content: str
    source: str
    metadata: dict


@dataclass
class ChildChunk:
    """Small embedding unit with parent reference."""
    child_id: str
    parent_id: str
    content: str
    metadata: dict


def _semantic_split(text: str, max_size: int, overlap: int) -> List[str]:
    """Split text by sentences/paragraphs when possible to respect semantics."""
    if not text or not text.strip():
        return []
    # Prefer splitting on double newline, then single newline, then sentence end
    segments = re.split(r'\n\n+|\n|(?<=[.!?])\s+', text)
    chunks = []
    current = []
    current_len = 0
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        seg_len = len(seg) + 1
        if current_len + seg_len > max_size and current:
            chunk_text = " ".join(current)
            chunks.append(chunk_text)
            # Overlap: keep last N chars worth of segments
            overlap_len = 0
            new_current = []
            for s in reversed(current):
                if overlap_len + len(s) <= overlap:
                    new_current.insert(0, s)
                    overlap_len += len(s)
                else:
                    break
            current = new_current
            current_len = sum(len(s) for s in current)
        current.append(seg)
        current_len += seg_len
    if current:
        chunks.append(" ".join(current))
    return chunks


def create_parent_chunks(
    text: str,
    source: str = "unknown",
    chunk_size: int = 2000,
    overlap: int = 200,
    metadata: dict = None,
) -> List[ParentChunk]:
    """Create parent chunks (large semantic sections)."""
    raw_chunks = _semantic_split(text, chunk_size, overlap)
    parents = []
    for i, content in enumerate(raw_chunks):
        parent_id = f"parent_{uuid.uuid4().hex[:12]}"
        parents.append(ParentChunk(
            parent_id=parent_id,
            content=content.strip(),
            source=source,
            metadata=metadata or {},
        ))
    return parents


def create_child_chunks(
    parent_chunks: List[ParentChunk],
    chunk_size: int = 256,
    overlap: int = 50,
) -> List[ChildChunk]:
    """Create child chunks from parent chunks; each child retains parent_id."""
    def _title_from_parent(text: str) -> str:
        if not text:
            return ""
        # Prefer first non-empty line; fallback to first sentence
        for line in text.splitlines():
            l = line.strip()
            if l:
                first = l
                break
        else:
            first = text.strip()
        # Shorten to ~30 tokens
        tokens = first.split()
        return " ".join(tokens[:30])

    children = []
    for parent in parent_chunks:
        raw = _semantic_split(parent.content, chunk_size, overlap)
        prefix = _title_from_parent(parent.content)
        for j, content in enumerate(raw):
            child_id = f"child_{uuid.uuid4().hex[:12]}"
            enriched = (prefix + "\n\n" + content.strip()).strip() if prefix else content.strip()
            children.append(ChildChunk(
                child_id=child_id,
                parent_id=parent.parent_id,
                content=enriched,
                metadata={"source": parent.source, "index": j, **parent.metadata},
            ))
    return children


def parent_child_chunk(
    text: str,
    source: str = "unknown",
    parent_size: int = 2000,
    parent_overlap: int = 200,
    child_size: int = 256,
    child_overlap: int = 50,
    metadata: dict = None,
) -> Tuple[List[dict], List[dict]]:
    """
    Produce parent and child chunk lists as dicts for storage.
    Returns (parent_dicts, child_dicts).
    """
    parents = create_parent_chunks(
        text, source=source,
        chunk_size=parent_size, overlap=parent_overlap,
        metadata=metadata,
    )
    children = create_child_chunks(parents, chunk_size=child_size, overlap=child_overlap)
    return [asdict(p) for p in parents], [asdict(c) for c in children]
