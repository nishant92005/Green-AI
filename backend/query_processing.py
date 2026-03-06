"""Query processing: multi-query expansion and HyDE hypothetical answer generation.

Uses Groq for fast LLM utilities, feeding into cosine-similarity retrieval.
"""

from typing import List

from .config import MULTI_QUERY_COUNT
from .groq_client import chat_single


def expand_queries(query: str, num_variations: int = None) -> List[str]:
    """Generate 3–5 query variations via Groq to enrich retrieval."""
    num = num_variations or min(max(MULTI_QUERY_COUNT, 3), 5)
    prompt = f"""You are an environmental and construction risk analyst. Given the user question below, generate {num} alternative phrasings that capture the same intent. Output ONLY the alternative questions, one per line, no numbering or bullets.

User question: {query}"""
    try:
        text = chat_single(prompt, temperature=0.5, max_tokens=300)
        lines = [l.strip() for l in (text or "").split("\n") if l.strip()]
        cleaned = []
        for line in lines[:num]:
            for sep in (". ", ") ", "- ", " "):
                if line.startswith(sep) or (len(sep) > 1 and sep in line and line.find(sep) < 4):
                    line = line.split(sep, 1)[-1].strip()
                    break
            cleaned.append(line)
        return [query] + cleaned[: num - 1]
    except Exception:
        return [query]


def generate_hyde(query: str) -> str:
    """Generate a hypothetical ideal answer for the query (HyDE) to embed using Groq."""
    prompt = f"""You are Green AI, an environmental and construction risk analyst. Write a short, factual paragraph that would be the ideal answer to this question (as if from a report). Do not say you don't have the document. Write 2-4 sentences only.

Question: {query}"""
    try:
        text = chat_single(prompt, temperature=0.4, max_tokens=200)
        return (text or "").strip() or query
    except Exception:
        return query
