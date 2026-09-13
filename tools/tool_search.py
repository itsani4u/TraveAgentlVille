"""
tools/tool_search.py
---------------------
A tiny helper that lets the agent (or a student debugging it) look up which
registered tool best matches a plain-English need, e.g. "I need the weather"
-> get_weather_tool. This is intentionally simple keyword matching, not an
embedding search - the knowledge-base retriever (tool_retrieval/) is where
real semantic search is demonstrated.
"""

from tools.tool_registry import TOOL_REGISTRY

_KEYWORDS = {
    "get_weather_tool": ["weather", "forecast", "rain", "temperature"],
    "search_activities_tool": ["search", "find activity", "interest", "catalog"],
    "get_activities_by_date_tool": ["events", "scheduled", "happening on"],
    "run_evals_tool": ["validate", "check", "evaluate", "eval"],
    "final_answer_tool": ["final", "done", "finish", "submit"],
}


def find_tool(query: str) -> str:
    """Return the tool name that best matches a natural-language query."""
    query_lower = query.lower()
    best_tool, best_score = "run_evals_tool", 0
    for tool_name, keywords in _KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > best_score:
            best_tool, best_score = tool_name, score
    return best_tool


def list_tools() -> list:
    """List every tool name currently registered."""
    return list(TOOL_REGISTRY.keys())
