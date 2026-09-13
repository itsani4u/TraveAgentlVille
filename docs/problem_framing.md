# Problem Framing

## The problem
Planning a multi-day trip means juggling three moving parts at once:
budget, weather, and personal interests. Doing this by hand means a lot of
tab-switching between weather sites, activity listings, and a spreadsheet.

## The AgentsVille solution
AgentsVille is a fictional city used as a safe sandbox: we can invent
weather and activity data without needing real API keys, while still
practicing the full agentic pattern a real travel app would use.

The pipeline has three stages:

1. **Draft.** An Itinerary Agent turns a traveler's `VacationInfo` (dates,
   budget, interests) into a first-pass itinerary using chain-of-thought
   prompting.
2. **Revise.** A ReAct agent inspects the draft with a `run_evals_tool`,
   and if something's wrong (a thin day, a rain-soaked hike) it looks up
   weather and alternate activities and patches the plan - looping until
   the evals pass.
3. **Narrate.** A final LLM call turns the validated JSON itinerary into a
   short, readable trip summary a human would actually enjoy reading.

## Why this is a good teaching project
- Shows structured generation (Pydantic + JSON) alongside free-form
  generation (the narrative).
- Shows a real ReAct loop with explicit THOUGHT/ACTION/OBSERVATION turns,
  not hidden behind a framework's black box.
- Adds a light RAG layer (FAISS + Gemini embeddings) so students see how a
  knowledge base can ground answers.
- Adds a minimal policy/RLHF loop so students see how user feedback could,
  in principle, change agent behavior over time.
- Adds DeepEval so "did the agent actually do a good job" becomes a
  measurable, repeatable question instead of a vibe check.
