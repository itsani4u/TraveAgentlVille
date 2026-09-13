"""
policy_rlhf/policy_checker.py
-------------------------------
Loads the business-rule "policy" (data/policy/policy.json) and exposes a
tiny helper to check a value against a named rule. Keeping rules in a JSON
file (instead of hard-coded constants) is what lets policy_updater.py
change them later based on collected feedback, without touching code.
"""

import json
from typing import Any, Dict

import config


def load_policy() -> Dict:
    with open(config.DATA_POLICY_PATH, "r") as f:
        return json.load(f)


def get_rule_value(rule_id: str) -> Any:
    policy = load_policy()
    for rule in policy["rules"]:
        if rule["id"] == rule_id:
            return rule["value"]
    raise KeyError(f"No policy rule named '{rule_id}'")


def check_min_activities(num_activities: int) -> bool:
    return num_activities >= get_rule_value("min_activities_per_day")


def check_trip_length(num_days: int) -> bool:
    return num_days <= get_rule_value("max_trip_length_days")


def is_weather_blocked(condition: str) -> bool:
    return condition in get_rule_value("outdoor_weather_blocklist")
