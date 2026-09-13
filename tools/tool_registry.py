"""
tools/tool_registry.py
-----------------------
The 5 mock tools the ReAct Revision Agent can call (see SRS section 4).

They are "mock" because AgentsVille is a fictional city - there is no real
weather API or activities catalog. Everything here is deterministic,
in-memory fake data generated from simple hashing, which keeps the demo
reproducible and free to run.

Each function is wrapped with LangChain's @tool decorator so it can also be
plugged straight into a LangChain AgentExecutor if you want to experiment
with that instead of the custom ReAct loop in agent/core_agent.py.
"""

import json
import random
import hashlib
from datetime import date
from typing import Dict, List

from langchain_core.tools import tool

# ---------------------------------------------------------------------
# Fake catalogs (deterministic, seeded from date/interest strings so the
# same inputs always produce the same "random" answer)
# ---------------------------------------------------------------------

_WEATHER_CONDITIONS = ["sunny", "partly cloudy", "light rain", "storm", "clear", "heavy snow"]

_ACTIVITY_BANK = {
    "art": ["AgentsVille Modern Art Museum", "Street Mural Walking Tour", "Pottery Workshop"],
    "food": ["Night Market Food Crawl", "Pasta Making Class", "Rooftop Tasting Menu"],
    "hiking": ["Cascade Ridge Trail", "Old Quarry Loop Hike", "Sunrise Summit Trek"],
    "history": ["AgentsVille Old Town Tour", "War Memorial Museum", "Founders' Archive Visit"],
    "music": ["Jazz Cellar Night", "Symphony at the Grand Hall", "Busking District Stroll"],
    "default": ["City Sightseeing Bus", "Central Park Picnic", "Local Craft Market"],
}


def _seeded_random(seed_text: str) -> random.Random:
    seed_int = int(hashlib.sha256(seed_text.encode()).hexdigest(), 16) % (10 ** 8)
    return random.Random(seed_int)


@tool
def get_weather_tool(location: str, date_str: str) -> str:
    """Returns forecasted weather conditions for a given AgentsVille date.
    Args: location (str), date_str (str, format YYYY-MM-DD)."""
    rng = _seeded_random(f"weather-{location}-{date_str}")
    condition = rng.choice(_WEATHER_CONDITIONS)
    temp_c = rng.randint(-5, 40)
    return json.dumps({"location": location, "date": date_str, "condition": condition, "temp_c": temp_c})


@tool
def search_activities_tool(location: str, interest: str) -> str:
    """Returns catalog activities in AgentsVille matching a traveler interest.
    Args: location (str), interest (str, e.g. 'art', 'food', 'hiking')."""
    options = _ACTIVITY_BANK.get(interest.lower(), _ACTIVITY_BANK["default"])
    rng = _seeded_random(f"search-{location}-{interest}")
    results = [
        {
            "name": name,
            "cost": round(rng.uniform(10, 120), 2),
            "is_outdoor": rng.random() > 0.5,
            "matched_interest": interest,
        }
        for name in options
    ]
    return json.dumps(results)


@tool
def get_activities_by_date_tool(date_str: str) -> str:
    """Returns AgentsVille's scheduled public events happening on a date.
    Args: date_str (str, format YYYY-MM-DD)."""
    rng = _seeded_random(f"events-{date_str}")
    all_events = [e for events in _ACTIVITY_BANK.values() for e in events]
    picked = rng.sample(all_events, k=2)
    results = [
        {"name": name, "cost": round(rng.uniform(0, 80), 2), "is_outdoor": rng.random() > 0.5}
        for name in picked
    ]
    return json.dumps(results)


@tool
def run_evals_tool(itinerary_json: str) -> str:
    """Validates a TravelPlan JSON string: every day must have >= 2
    activities and no outdoor activity may sit on a storm/heavy-snow day
    (weather is re-checked live). Returns {"passed": bool, "issues": [...]}."""
    issues: List[str] = []
    try:
        plan = json.loads(itinerary_json)
    except json.JSONDecodeError as e:
        return json.dumps({"passed": False, "issues": [f"Invalid JSON: {e}"]})

    day_plans = plan.get("day_plans", [])
    if not day_plans:
        issues.append("No day_plans found in itinerary.")

    for day in day_plans:
        activities = day.get("activities", [])
        day_date = day.get("date", "unknown")
        if len(activities) < 2:
            issues.append(f"Day {day_date} has fewer than 2 activities.")
        for act in activities:
            if act.get("is_outdoor"):
                weather = json.loads(get_weather_tool.invoke({"location": "AgentsVille", "date_str": day_date}))
                if weather["condition"] in ("storm", "heavy snow"):
                    issues.append(
                        f"Outdoor activity '{act.get('name')}' on {day_date} conflicts with {weather['condition']}."
                    )

    total_cost = sum(a.get("cost", 0) for day in day_plans for a in day.get("activities", []))
    budget = plan.get("vacation_info", {}).get("total_budget")
    if budget is not None and total_cost > budget:
        issues.append(f"Total cost {total_cost} exceeds budget {budget}.")

    return json.dumps({"passed": len(issues) == 0, "issues": issues})


@tool
def final_answer_tool(revised_itinerary: str) -> str:
    """Exits the ReAct loop and returns the finalized itinerary JSON string
    unchanged. Only call this after run_evals_tool reports passed=true."""
    return revised_itinerary


# A simple name -> callable registry, used by the custom ReAct loop in
# agent/core_agent.py so it can dispatch ACTION calls by tool name.
TOOL_REGISTRY: Dict[str, object] = {
    "get_weather_tool": get_weather_tool,
    "search_activities_tool": search_activities_tool,
    "get_activities_by_date_tool": get_activities_by_date_tool,
    "run_evals_tool": run_evals_tool,
    "final_answer_tool": final_answer_tool,
}
