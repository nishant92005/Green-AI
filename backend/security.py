"""Security layer: prompt injection detection and input sanitization."""

import re
from typing import Tuple

# Patterns that often indicate prompt injection or malicious override attempts
BLOCKED_PATTERNS = [
    r"ignore\s+(previous|all|above|prior)\s+instructions",
    r"disregard\s+(previous|all|your)\s+",
    r"forget\s+(everything|your|all)",
    r"bypass\s+(security|safety|content\s+filter)",
    r"override\s+(system|model|instructions)",
    r"you\s+are\s+now\s+",
    r"pretend\s+(you\s+are|to\s+be)",
    r"act\s+as\s+if\s+you\s+(are|were)",
    r"system\s*:\s*",
    r"\[INST\]",
    r"<\|.*\|>",
    r"jailbreak",
    r"dan\s+mode",
    r"do\s+anything\s+now",
    r"output\s+(only|just)\s+(the|as)\s+",
]

BLOCKED_PATTERNS_COMPILED = [re.compile(p, re.I) for p in BLOCKED_PATTERNS]


def detect_prompt_injection(text: str) -> bool:
    """Return True if potential prompt injection is detected."""
    if not text or not isinstance(text, str):
        return False
    t = text.strip()
    for pat in BLOCKED_PATTERNS_COMPILED:
        if pat.search(t):
            return True
    return False


def sanitize_input(text: str) -> Tuple[str, bool]:
    """
    Sanitize user input and check for prompt injection.
    Returns (sanitized_text, is_safe). If not safe, sanitized_text is a safe placeholder message.
    """
    if text is None:
        return "", True
    if not isinstance(text, str):
        text = str(text)
    # Normalize whitespace
    sanitized = " ".join(text.split())
    # Truncate to prevent abuse
    max_len = 2000
    if len(sanitized) > max_len:
        sanitized = sanitized[:max_len]
    if detect_prompt_injection(sanitized):
        return "I can only answer questions about environmental and construction risk analysis. Please rephrase your question.", False
    return sanitized, True

