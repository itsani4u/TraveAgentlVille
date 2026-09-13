# Engineering Justification

## Why LangChain
- `ChatGoogleGenerativeAI` and `GoogleGenerativeAIEmbeddings` give a single,
  consistent interface to Gemini for both chat completions and embeddings,
  so `agent/` and `tool_retrieval/` code doesn't need to hand-roll HTTP
  calls to the Gemini API.
- The `@tool` decorator and `FAISS` vector store integration mean the same
  tool objects could be dropped straight into a LangChain `AgentExecutor`
  later, without rewriting them - useful if a class wants to compare the
  hand-rolled ReAct loop against LangChain's built-in one.

## Why a hand-written ReAct loop instead of AgentExecutor
The SRS (FR-4) requires explicit `THOUGHT` and `ACTION` sections in a
single response turn, and a guaranteed `run_evals_tool` call both before
and after any fix. Writing the loop by hand in `agent/core_agent.py` makes
every step visible and debuggable for students, and makes it trivial to
enforce "must call run_evals_tool before final_answer_tool" as an explicit
`if` check rather than trusting a framework's internal policy.

## Why FAISS (not a managed vector DB)
This is a teaching project meant to run locally or in a single Cloud Run
container with no extra managed services. FAISS needs no server, persists
to two small files (`index.faiss`, `index.pkl`), and is fast enough for the
handful of documents a course would realistically upload.

## Why json-repair
LLMs occasionally emit almost-valid JSON (a trailing comma, an unescaped
quote). Rather than retry the whole generation, `json_repair.repair_json()`
fixes small syntax issues in milliseconds before the string reaches
Pydantic - this keeps the app fast and avoids extra LLM cost from retries.

## Why Pydantic schemas everywhere
`VacationInfo`, `TravelPlan`, `DayPlan`, `Activity` are all Pydantic models
so that every stage of the pipeline - draft, revise, evaluate - is
validating against the exact same structure. If the schema ever needs a
new field, it changes in one file (`agent/schemas.py`) and every consumer
gets the update automatically.

## Why DeepEval
DeepEval gives LLM-as-judge metrics (answer relevancy, faithfulness) out
of the box, plus a simple `assert_test` pattern that mirrors normal Python
testing - so `evaluation/deepeval_metrics.py` can sit next to a pytest
suite without students needing to learn a separate eval framework.

## Why a separate policy_rlhf/ module
Keeping "what rules should the agent enforce" (data-driven, in
`policy.json`) separate from "how does the agent enforce them" (code, in
`tools/tool_registry.py` and `safety/guardrails.py`) is a pattern worth
demonstrating early: it's what lets a feedback loop change behavior later
without a code deploy.
