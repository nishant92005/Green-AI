"""LLM generation with Ollama (local, e.g. qwen2.5:3b)."""

import re
from typing import Tuple

from .ollama_client import generate

SYSTEM_PROMPT = """You are Green AI, an intelligent environmental and construction risk analyst.

You MUST:
- Base your answer ONLY on the provided context from the uploaded documents (PPT, PDF, images after OCR). Do not use external knowledge.
- If some information is not present in the context, explicitly say "Not specified in the provided document" instead of guessing.
- Prefer quoting or paraphrasing concrete details from the document (section names, key topics, important phrases, important constraints).

Formatting rules:
- Do NOT use any markdown formatting characters like #, ##, ###, **, *, or bullet lists. Write plain text only.
- Structure your answer as short text headings followed by content, for example:
  Overview:
  <paragraph>

  Key Points:
  <paragraphs describing main sections / topics from the document>

  Environmental Assessment (AQI, deforestation, pollution, etc.):
  <paragraphs describing exactly what the document says; if silent, say it is not specified>

  Recommendations:
  <paragraphs, only if grounded in the context>

Risk score:
- Always end your response with a risk score on its own line: Risk Score: Low, Risk Score: Medium, or Risk Score: High.
- The risk score must be consistent with what the context actually states."""


def extract_risk_score(text: str) -> str:
    """Parse Risk Score: X from model output."""
    if not text:
        return "Medium"
    match = re.search(r"Risk\s*Score\s*:\s*(Low|Medium|High)", text, re.I)
    if match:
        return match.group(1).strip().capitalize()
    return "Medium"


def strip_markdown(text: str) -> str:
    """Remove common markdown markers like ### and ** to return clean plain text."""
    if not text:
        return ""
    cleaned_lines = []
    for line in text.splitlines():
        l = line.lstrip()
        while l.startswith("#"):
            l = l[1:].lstrip()
        l = l.replace("**", "")
        l = re.sub(r"^\s*[-*•]\s+", "", l)
        l = re.sub(r"^\s*\d+\.\s+", "", l)
        cleaned_lines.append(l)
    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def generate_answer(context: str, query: str) -> Tuple[str, str]:
    """
    Build prompt with ranked context and user query; generate response via Ollama.
    Returns (full_response_text, risk_score).
    """
    if not context.strip():
        context = "(No specific documents were retrieved. Base your answer on general environmental and construction risk knowledge, and indicate uncertainty where appropriate.)"

    user_content = f"""Context from knowledge base (excerpts from the uploaded documents):
{context}

User question: {query}

Provide a clear, grounded answer using ONLY the information from the context above. Follow the formatting rules and end with exactly one line: Risk Score: Low, Risk Score: Medium, or Risk Score: High."""

    full_text = generate(
        prompt=user_content,
        system=SYSTEM_PROMPT,
        max_tokens=1024,
        temperature=0.3,
    )
    full_text = strip_markdown(full_text or "")
    risk = extract_risk_score(full_text)
    return full_text, risk
