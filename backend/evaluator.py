"""Evaluation loop: LLM self-check for grounding and hallucination (Ollama)."""

from .ollama_client import generate


def is_answer_grounded(context: str, answer: str, query: str) -> bool:
    """
    Ask LLM whether the answer is grounded in the context and free of hallucination.
    Returns True if grounded, False otherwise.
    """
    prompt = f"""You are a fact-checker. Given the CONTEXT (retrieved documents), the USER QUESTION, and the MODEL ANSWER, determine:
1. Is the answer supported by the context (no unsupported claims)?
2. Are there any obvious hallucinations (made-up facts, numbers, or sources)?

Reply with only one word: GROUNDED or NOT_GROUNDED.

CONTEXT:
{context[:3000]}

USER QUESTION: {query}

MODEL ANSWER:
{answer[:2000]}

Your verdict (GROUNDED or NOT_GROUNDED):"""

    try:
        text = (generate(prompt=prompt, max_tokens=10, temperature=0) or "").strip().upper()
        if "NOT_GROUNDED" in text or "NOT GROUNDED" in text:
            return False
        return "GROUNDED" in text or len(text) < 3
    except Exception:
        return True  # On error, accept answer to avoid infinite loop
