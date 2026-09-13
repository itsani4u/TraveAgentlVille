"""
safety/guardrails.py
----------------------
Simple input/output guardrails for the trip planner agent:
- blocks obviously off-topic or unsafe requests before they reach the LLM
- checks that budget and dates are sane before generation starts
- scrubs PII from anything that will be written to logs
"""

from datetime import date
from typing import Tuple

from safety.pii_filter import redact_pii

_BLOCKED_KEYWORDS = ["hack", "bomb", "weapon", "exploit", "malware"]


def check_input_safety(user_text: str) -> Tuple[bool, str]:
    """Returns (is_safe, reason). Blocks requests containing unsafe
    keywords; everything else passes through."""
    lowered = user_text.lower()
    for kw in _BLOCKED_KEYWORDS:
        if kw in lowered:
            return False, f"Request blocked: contains disallowed term '{kw}'."
    return True, "ok"


def validate_vacation_dates(start_date: date, end_date: date) -> Tuple[bool, str]:
    """Basic sanity checks on trip dates."""
    if end_date < start_date:
        return False, "end_date must be on or after start_date."
    if (end_date - start_date).days > 30:
        return False, "Trips longer than 30 days are not supported in this demo."
    return True, "ok"


def validate_budget(total_budget: float) -> Tuple[bool, str]:
    if total_budget <= 0:
        return False, "total_budget must be greater than zero."
    return True, "ok"


def safe_for_logging(text: str) -> str:
    """Redact PII before writing anything to the log files."""
    return redact_pii(text)
