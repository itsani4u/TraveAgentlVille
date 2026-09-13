"""
agent/planner.py
------------------
The two "one-shot" LLM agents from the SRS:

- Itinerary Agent   (FR-2): VacationInfo -> draft TravelPlan JSON
- Compatibility Agent (FR-3): one Activity + weather -> compatible? why?

Both use Gemini via LangChain's ChatGoogleGenerativeAI, low temperature,
and json-repair to gracefully clean up any near-miss JSON before Pydantic
validates it (NFR-1).
"""

import json
from json_repair import repair_json
from langchain_google_genai import ChatGoogleGenerativeAI

import config
from agent.prompts import ITINERARY_AGENT_SYSTEM_PROMPT, ACTIVITY_AND_WEATHER_ARE_COMPATIBLE_SYSTEM_PROMPT
from agent.schemas import VacationInfo, TravelPlan, Activity, CompatibilityResult


def get_llm(temperature: float = None) -> ChatGoogleGenerativeAI:
    """One place that builds the Gemini chat model, so every agent stays consistent."""
    return ChatGoogleGenerativeAI(
        model=config.GEMINI_LLM_MODEL,
        google_api_key=config.GOOGLE_API_KEY,
        temperature=temperature if temperature is not None else config.LLM_TEMPERATURE,
    )


def _clean_json(raw_text: str) -> dict:
    """Strip markdown fences (if the model added them anyway) and repair
    minor JSON issues before parsing."""
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json\n", "", 1) if text.startswith("json\n") else text
    repaired = repair_json(text)
    return json.loads(repaired)


def generate_initial_itinerary(vacation_info: VacationInfo) -> TravelPlan:
    """FR-2: ask the Itinerary Agent for a first-draft TravelPlan."""
    llm = get_llm()
    user_prompt = (
        f"VacationInfo:\n{vacation_info.model_dump_json(indent=2)}\n\n"
        f"Number of days in trip: {vacation_info.num_days()}\n"
        "Produce the TravelPlan JSON now."
    )
    response = llm.invoke(
        [
            {"role": "system", "content": ITINERARY_AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    )
    parsed = _clean_json(response.content)
    return TravelPlan.model_validate(parsed)


def check_activity_weather_compatibility(activity: Activity, weather_condition: str, activity_date) -> CompatibilityResult:
    """FR-3: ask the Compatibility Agent whether one activity is safe given the weather."""
    llm = get_llm()
    user_prompt = json.dumps(
        {
            "activity": activity.model_dump(),
            "weather_condition": weather_condition,
            "date": str(activity_date),
        }
    )
    response = llm.invoke(
        [
            {"role": "system", "content": ACTIVITY_AND_WEATHER_ARE_COMPATIBLE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    )
    parsed = _clean_json(response.content)
    return CompatibilityResult(
        activity_name=activity.name,
        date=activity_date,
        is_compatible=parsed["is_compatible"],
        justification=parsed["justification"],
    )


def generate_narrative_summary(travel_plan: TravelPlan) -> str:
    """FR-5: turn a finalized TravelPlan into a friendly prose summary."""
    from agent.prompts import NARRATIVE_SUMMARY_SYSTEM_PROMPT

    llm = get_llm(temperature=0.5)  # a little more creative freedom for prose
    response = llm.invoke(
        [
            {"role": "system", "content": NARRATIVE_SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": travel_plan.model_dump_json(indent=2)},
        ]
    )
    return response.content
