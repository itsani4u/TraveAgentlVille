"""
safety/pii_filter.py
----------------------
Very small, regex-based PII scrubber for a student project. Not meant to be
production-grade - just enough to demonstrate the idea of catching emails,
phone numbers, and credit-card-like numbers before they hit a log file or
get sent to the LLM.
"""

import re

_PATTERNS = {
    "EMAIL": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "PHONE": re.compile(r"\b(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "CREDIT_CARD": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
}


def redact_pii(text: str) -> str:
    """Replace any detected PII in `text` with a [REDACTED_<TYPE>] tag."""
    redacted = text
    for label, pattern in _PATTERNS.items():
        redacted = pattern.sub(f"[REDACTED_{label}]", redacted)
    return redacted


def contains_pii(text: str) -> bool:
    """True if any PII pattern matches inside `text`."""
    return any(pattern.search(text) for pattern in _PATTERNS.values())
