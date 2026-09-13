# AgentsVille Trip Planner

An agentic trip-planning demo built for learning: LangChain + Gemini (LLM
and embeddings) + a hand-written ReAct loop + FAISS retrieval + DeepEval,
wrapped in a small Streamlit UI, deployable to GCP Cloud Run.

See `AgentVille.txt`-style requirements in `docs/problem_framing.md` for
the full problem statement this implements.

## What it does

1. **Draft** - an Itinerary Agent turns your trip details (dates, budget,
   interests) into a first-pass day-by-day itinerary (strict JSON, via
   Gemini + Pydantic).
2. **Revise** - a ReAct Revision Agent checks the draft with
   `run_evals_tool` (budget, weather conflicts, min. 2 activities/day) and
   fixes anything wrong by calling weather/activity-search tools, looping
   until the plan passes.
3. **Narrate** - a final LLM call turns the validated itinerary into a
   friendly prose summary.
4. Optionally, ask questions grounded in your own uploaded documents via a
   small Gemini + FAISS RAG pipeline.
5. Thumbs up/down feedback feeds a tiny rule-based "policy" loop
   (`policy_rlhf/`) that can tighten business rules over time.
6. `evaluation/deepeval_metrics.py` scores itinerary quality with both
   deterministic checks and DeepEval's LLM-judge metrics.

## Project layout

```
travel_agentville/
├── agent/            # schemas, prompts, memory, planner (draft/narrate), ReAct core loop
├── tools/             # the 5 mock tools the ReAct agent can call
├── tool_retrieval/    # PDF loading -> chunking -> Gemini embeddings -> FAISS -> retrieval
├── policy_rlhf/       # policy.json rules + feedback store + a toy policy-update loop
├── safety/            # input guardrails + a small PII redactor
├── evaluation/        # DeepEval + deterministic checks
├── streamlit_app/     # the 3-page UI: ingestion, index build, chat
├── knowledge/         # raw/ processed/ faiss_index/ (mostly empty until you use the app)
├── data/              # policy.json, feedback_store.json, eval_rubric.json
├── docs/              # design docs (framing, prompts, evaluation, justification, demo script)
├── logs/              # interactions/policy-change/error logs
├── config.py          # all settings, loaded from .env
├── Dockerfile
├── docker-compose.yml # local container run
├── app.yaml           # Cloud Run (Knative) service definition
└── cloudbuild.yaml    # optional CI/CD: build + push + deploy
```

## Quickstart (local)

```bash
cp .env.example .env        # then edit .env and add your GOOGLE_API_KEY
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app/app.py
```

Open the URL Streamlit prints, then:
1. Go to **1. Data Ingestion**, upload a PDF/txt/md about AgentsVille.
2. Go to **2. Build Index** and click "Build / Rebuild Index".
3. Go to **3. Chat**, plan a trip, and try the knowledge-base Q&A tab.

## Running the evaluation suite

```bash
python -m evaluation.deepeval_metrics
```

## Running with Docker

```bash
docker compose up --build
```

## Deploying to GCP Cloud Run

```bash
# 1. Build & push the image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/agentsville-trip-planner

# 2. Edit app.yaml: replace YOUR_PROJECT_ID with your real project id

# 3. Deploy
gcloud run services replace app.yaml --region=us-central1

# 4. Add your Gemini API key as a secret (recommended over plain env vars)
gcloud secrets create agentsville-gemini-key --data-file=<(echo -n "$GOOGLE_API_KEY")
gcloud run services update agentsville-trip-planner \
  --update-secrets=GOOGLE_API_KEY=agentsville-gemini-key:latest \
  --region=us-central1
```

Or let `cloudbuild.yaml` do steps 1 and 3 automatically via
`gcloud builds submit --config cloudbuild.yaml`.

## Environment variables

See `.env.example` for the full list (Gemini model names, GCP project /
bucket / region, temperature, max ReAct steps, log level).

## Notes for students

- Every module has a short docstring at the top explaining its one job -
  start at `agent/core_agent.py` to see the whole pipeline wired together,
  then follow the imports outward.
- `tools/tool_registry.py`'s tools are all mocked (AgentsVille isn't real),
  so the whole app runs without any paid API besides Gemini itself.
- `docs/engineering_justification.md` explains *why* each library/pattern
  was chosen, which is worth reading before you start modifying things.
