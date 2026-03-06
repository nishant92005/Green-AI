"""Document store for parent chunks (JSON-backed)."""

import json
from pathlib import Path
from typing import List, Dict, Any

from .config import DOCUMENT_STORE_PATH


def load_document_store(path: Path = None) -> List[Dict[str, Any]]:
    path = path or DOCUMENT_STORE_PATH
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_document_store(parents: List[Dict[str, Any]], path: Path = None) -> None:
    path = path or DOCUMENT_STORE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(parents, f, indent=2, ensure_ascii=False)


def get_parents_by_ids(parent_ids: List[str]) -> List[Dict[str, Any]]:
    """Return parent chunks for given parent_ids, preserving order where possible."""
    store = load_document_store()
    by_id = {p["parent_id"]: p for p in store}
    return [by_id[pid] for pid in parent_ids if pid in by_id]


def add_parents(new_parents: List[Dict[str, Any]]) -> None:
    store = load_document_store()
    store.extend(new_parents)
    save_document_store(store)
