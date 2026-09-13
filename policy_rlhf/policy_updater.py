"""
policy_rlhf/policy_updater.py
--------------------------------
A deliberately simple "RLHF -> policy" loop for teaching purposes:

  1. Look at collected feedback (feedback_collector.load_feedback()).
  2. If thumbs-down ratings mention "too few activities" more than a
     threshold number of times, bump min_activities_per_day by 1.
  3. Save the updated policy.json and log the change.

This is NOT real reinforcement learning - it's a rule-based stand-in that
shows students the shape of a feedback -> policy update pipeline without
needing a training job.
"""

import json
from datetime import datetime, timezone

import config
from policy_rlhf.feedback_collector import load_feedback
from policy_rlhf.policy_checker import load_policy

COMPLAINT_KEYWORD = "too few activities"
COMPLAINT_THRESHOLD = 3


def _save_policy(policy: dict) -> None:
    config.DATA_POLICY_PATH.write_text(json.dumps(policy, indent=2))


def _log_change(message: str) -> None:
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.LOGS_DIR / "policy_change.log", "a") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat()}  {message}\n")


def maybe_update_policy() -> bool:
    """Returns True if a policy change was made."""
    feedback = load_feedback()
    complaints = [
        f for f in feedback if f["rating"] == "down" and COMPLAINT_KEYWORD in f.get("comment", "").lower()
    ]

    if len(complaints) < COMPLAINT_THRESHOLD:
        return False

    policy = load_policy()
    for rule in policy["rules"]:
        if rule["id"] == "min_activities_per_day":
            old_value = rule["value"]
            rule["value"] = old_value + 1
            policy["version"] += 1
            _save_policy(policy)
            _log_change(
                f"min_activities_per_day raised {old_value} -> {rule['value']} "
                f"after {len(complaints)} matching complaints."
            )
            return True
    return False
