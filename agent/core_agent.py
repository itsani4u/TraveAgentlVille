"""
agent/core_agent.py
---------------------
The ReAct Revision Agent (FR-4) plus a top-level `plan_trip()` function that
runs the whole pipeline end to end:

    VacationInfo
        -> Itinerary Agent (planner.py)          [draft TravelPlan]
        -> ReAct Revision Agent (this file)       [fixed TravelPlan]
        -> Narrative Agent (planner.py)           [prose summary]

The ReAct loop below is written by hand (not LangChain's AgentExecutor) so
students can see every THOUGHT -> ACTION -> OBSERVATION step explicitly,
exactly as the SRS describes it.
"""

import json
import re
from json_repair import repair_json

import config
from agent.prompts import REACT_REVISION_AGENT_SYSTEM_PROMPT
from agent.memory import AgentMemory
from agent.schemas import VacationInfo, TravelPlan
from agent.planner import generate_initial_itinerary, generate_narrative_summary, get_llm
from tools.tool_registry import TOOL_REGISTRY


def _parse_action(llm_text: str) -> dict:
    """Pull the ACTION JSON out of a THOUGHT/ACTION formatted response."""
    match = re.search(r"ACTION:\s*(\{.*\})", llm_text, re.DOTALL)
    if not match:
        raise ValueError("No ACTION block found in the agent's response.")
    action_json = repair_json(match.group(1))
    return json.loads(action_json)


def _call_tool(action: dict) -> str:
    """Dispatch an ACTION dict {"tool": name, "args": {...}} to the real tool."""
    tool_name = action.get("tool")
    args = action.get("args", {})
    if tool_name not in TOOL_REGISTRY:
        return json.dumps({"error": f"Unknown tool '{tool_name}'. Valid tools: {list(TOOL_REGISTRY)}"})
    tool_fn = TOOL_REGISTRY[tool_name]
    try:
        return tool_fn.invoke(args)
    except Exception as e:
        # NFR-2: corrective observation instead of crashing the loop
        return json.dumps({"error": f"Tool call failed: {e}. Check your 'args' match the tool signature."})


def run_react_revision(draft_plan: TravelPlan, max_steps: int = None) -> TravelPlan:
    """FR-4: iteratively revise a draft TravelPlan using the ReAct loop
    until run_evals_tool passes, then return the finalized plan."""
    max_steps = max_steps or config.MAX_REACT_STEPS
    llm = get_llm()
    memory = AgentMemory()

    conversation = [{"role": "system", "content": REACT_REVISION_AGENT_SYSTEM_PROMPT}]
    conversation.append(
        {
            "role": "user",
            "content": f"Here is the draft itinerary to check and, if needed, revise:\n{draft_plan.model_dump_json()}",
        }
    )

    latest_itinerary_json = draft_plan.model_dump_json()

    for step in range(max_steps):
        response = llm.invoke(conversation)
        text = response.content
        memory.add_scratchpad_entry(text)

        try:
            action = _parse_action(text)
        except ValueError as e:
            # NFR-2: corrective observation, ask the model to reformat
            observation = f"OBSERVATION: {e} Please respond again with a THOUGHT and a valid ACTION JSON block."
            conversation.append({"role": "assistant", "content": text})
            conversation.append({"role": "user", "content": observation})
            continue

        if action.get("tool") == "final_answer_tool":
            latest_itinerary_json = action["args"].get("revised_itinerary", latest_itinerary_json)
            break

        if action.get("tool") in ("run_evals_tool",):
            # Always evaluate the *latest* itinerary the agent has produced so far.
            action.setdefault("args", {})["itinerary_json"] = action["args"].get("itinerary_json", latest_itinerary_json)

        observation_raw = _call_tool(action)
        memory.add_scratchpad_entry(f"OBSERVATION: {observation_raw}")

        # If the agent supplied a revised itinerary as part of its action args, track it.
        if "revised_itinerary" in action.get("args", {}):
            latest_itinerary_json = action["args"]["revised_itinerary"]
        if "itinerary_json" in action.get("args", {}) and action.get("tool") != "run_evals_tool":
            latest_itinerary_json = action["args"]["itinerary_json"]

        conversation.append({"role": "assistant", "content": text})
        conversation.append({"role": "user", "content": f"OBSERVATION: {observation_raw}"})
    else:
        # Loop exhausted max_steps without a final_answer_tool call.
        pass

    repaired = repair_json(latest_itinerary_json)
    return TravelPlan.model_validate(json.loads(repaired))


def plan_trip(vacation_info: VacationInfo) -> dict:
    """The full pipeline: draft -> revise -> narrate. Returns a dict with
    both the structured plan and the prose summary, ready for the UI."""
    draft_plan = generate_initial_itinerary(vacation_info)
    final_plan = run_react_revision(draft_plan)
    narrative = generate_narrative_summary(final_plan)
    return {
        "travel_plan": final_plan,
        "narrative": narrative,
    }
