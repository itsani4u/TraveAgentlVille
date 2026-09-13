# Evaluation Report Template

Fill this in after running `python -m evaluation.deepeval_metrics` (smoke
test) and a handful of real `plan_trip()` runs through the Streamlit UI.

## Deterministic checks (no LLM judge needed)
| Check | What it verifies | Pass rate observed |
|---|---|---|
| `schema_validity` | Output parses as a valid `TravelPlan` | _fill in_ |
| `budget_compliance` | Total cost <= `total_budget` | _fill in_ |
| `min_activities` | Every day has >= 2 activities | _fill in_ |

## DeepEval LLM-judged checks
| Metric | Threshold | Average score observed | Notes |
|---|---|---|---|
| Answer Relevancy | 0.7 | _fill in_ | Measures whether the narrative actually answers "what's my trip like" |
| Faithfulness | 0.7 | _fill in_ | Measures whether the narrative sticks to what's actually in the itinerary |

## Known failure modes to watch for
- Itinerary Agent occasionally wraps JSON in markdown fences despite being
  told not to - `json-repair` + fence-stripping in `planner.py` handles
  this, but log it if it still slips through.
- ReAct loop can exhaust `MAX_REACT_STEPS` without calling
  `final_answer_tool` on very tight budgets - in that case `core_agent.py`
  falls back to whatever the latest known itinerary was.
- Compatibility Agent can disagree with `run_evals_tool`'s own weather
  blocklist check since they're two separate reasoning paths - `run_evals_tool`
  is the source of truth used to gate `final_answer_tool`.

## How to re-run
```bash
python -m evaluation.deepeval_metrics
```
Or trigger a full run through Streamlit's chat page and record results
here manually.
