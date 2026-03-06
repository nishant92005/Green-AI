"""Ollama API client for local LLM (e.g. qwen2.5:3b)."""

import urllib.request
import json
from typing import Optional

from .config import OLLAMA_BASE_URL, OLLAMA_MODEL


def generate(
    prompt: str,
    system: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> str:
    """
    Call Ollama generate API. Returns the model's text response.
    If system is provided, it is prepended to the prompt.
    """
    if system:
        full_prompt = f"{system}\n\n{prompt}"
    else:
        full_prompt = prompt

    body = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": temperature,
        },
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            out = json.loads(resp.read().decode())
            return (out.get("response") or "").strip()
    except Exception as e:
        raise RuntimeError(f"Ollama request failed: {e}") from e
