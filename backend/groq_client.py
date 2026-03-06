"""Groq API client for utility LLM calls (query expansion, HyDE, etc.)."""

from typing import Optional

from groq import Groq

from .config import GROQ_API_KEY, GROQ_MODEL


_client: Optional[Groq] = None


def get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def chat_single(prompt: str, temperature: float = 0.4, max_tokens: int = 512) -> str:
    """Send a single-user-message chat completion and return the content text."""
    client = get_client()
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()

