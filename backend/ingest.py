"""Ingest documents: parent-child chunking, document store, vector store."""

from typing import Optional

from .chunking import parent_child_chunk
from .config import (
    PARENT_CHUNK_SIZE,
    PARENT_CHUNK_OVERLAP,
    CHILD_CHUNK_SIZE,
    CHILD_CHUNK_OVERLAP,
)
from .document_store import load_document_store, save_document_store, add_parents
from .embeddings import embed_batch
from .vector_store import add_children, load_from_disk, save_to_disk


def ingest_text(
    text: str,
    source: str = "upload",
    metadata: Optional[dict] = None,
) -> dict:
    """
    Chunk text into parents and children, store parents in document store,
    embed children and add to vector store. Optionally persist to disk.
    """
    parents, children = parent_child_chunk(
        text,
        source=source,
        parent_size=PARENT_CHUNK_SIZE,
        parent_overlap=PARENT_CHUNK_OVERLAP,
        child_size=CHILD_CHUNK_SIZE,
        child_overlap=CHILD_CHUNK_OVERLAP,
        metadata=metadata or {},
    )
    if not parents or not children:
        return {"parents_added": 0, "children_added": 0}

    add_parents(parents)
    vectors = embed_batch([c["content"] for c in children])
    add_children(children, vectors)
    try:
        save_to_disk()
    except Exception:
        pass
    return {"parents_added": len(parents), "children_added": len(children)}


def load_existing_index() -> bool:
    """Load FAISS index and children from disk if present."""
    return load_from_disk()
