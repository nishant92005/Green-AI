"""Context re-ranking via LLM relevance scoring (Groq for speed)."""

from typing import List

from .config import TOP_N_CONTEXTS
from .groq_client import chat_single


def rerank(
    query: str,
    context_strings: List[str],
    top_n: int = None,
) -> List[str]:
    """
    Re-rank context passages by relevance to query using LLM scoring.
    Returns top_n contexts in order of relevance.
    """
    n = top_n or TOP_N_CONTEXTS
    if not context_strings:
        return []
    if len(context_strings) <= n:
        return context_strings

    numbered = "\n".join([f"[{i+1}] {c[:800]}" for i, c in enumerate(context_strings)])
    prompt = f"""You are a relevance judge for environmental and construction risk analysis. Given the user question and the following context passages, output the indices of the {n} most relevant passages, in order of relevance (most first). Output ONLY a comma-separated list of numbers, e.g. 3,1,5,2,4.

User question: {query}

Passages:
{numbered}

Top {n} indices (comma-separated):"""

    try:
        text = (chat_single(prompt, temperature=0.0, max_tokens=50) or "").strip()
        indices = []
        for part in text.replace(".", ",").split(","):
            part = part.strip()
            if part.isdigit():
                idx = int(part) - 1
                if 0 <= idx < len(context_strings) and idx not in indices:
                    indices.append(idx)
        result = [context_strings[i] for i in indices[:n]]
        for i in range(len(context_strings)):
            if len(result) >= n:
                break
            if i not in indices:
                result.append(context_strings[i])
        return result[:n]
    except Exception:
        return context_strings[:n]
