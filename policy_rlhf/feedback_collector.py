"""
policy_rlhf/feedback_collector.py
------------------------------------
Very small RLHF-style feedback store: every time a user thumbs-up /
thumbs-down an itinerary in the Streamlit chat UI, we append a record here.
policy_updater.py can later read this file to decide whether a policy rule
needs adjusting (e.g. "users keep rejecting 3-activity days -> raise the
minimum").
"""

import json
from datetime import datetime, timezone
from typing import Optional

import config


def record_feedback(itinerary_summary: str, rating: str, comment: Optional[str] = None) -> None:
    """rating should be 'up' or 'down'."""
    config.DATA_RLHF_PATH.parent.mkdir(parents=True, exist_ok=True)
    if config.DATA_RLHF_PATH.exists():
        history = json.loads(config.DATA_RLHF_PATH.read_text() or "[]")
    else:
        history = []

    history.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "itinerary_summary": itinerary_summary[:500],
            "rating": rating,
            "comment": comment or "",
        }
    )
    config.DATA_RLHF_PATH.write_text(json.dumps(history, indent=2))


def load_feedback() -> list:
    if not config.DATA_RLHF_PATH.exists():
        return []
    return json.loads(config.DATA_RLHF_PATH.read_text() or "[]")
