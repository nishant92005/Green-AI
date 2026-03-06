"""Embedding model for text (and optional multimodal)."""

from typing import List, Union
import numpy as np

from sentence_transformers import SentenceTransformer

from .config import EMBEDDING_MODEL, EMBEDDING_DIM

_model = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def embed_text(text: str) -> np.ndarray:
    """Single text to vector."""
    return _get_model().encode(text, convert_to_numpy=True)


def embed_batch(texts: List[str], batch_size: int = 32) -> np.ndarray:
    """Batch of texts to matrix (n, dim)."""
    if not texts:
        return np.zeros((0, EMBEDDING_DIM), dtype=np.float32)
    return _get_model().encode(texts, batch_size=batch_size, convert_to_numpy=True)


def get_embedding_dim() -> int:
    return EMBEDDING_DIM
