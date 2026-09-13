# Demo Script (5-7 minutes)

1. **Setup (30s)**
   - `cp .env.example .env`, fill in `GOOGLE_API_KEY`.
   - `pip install -r requirements.txt`
   - `streamlit run streamlit_app/app.py`

2. **Ingestion page (1 min)**
   - Upload a sample PDF (e.g. a fictional "AgentsVille Visitor Guide").
   - Click "Upload to GCP bucket" - show the file lands in the configured
     GCS bucket (or note it will once real GCP credentials are attached).

3. **Index creation page (1 min)**
   - Click "Build / Rebuild Index".
   - Show the chunk count and that `knowledge/faiss_index/index.faiss`
     + `index.pkl` now exist.

4. **Chat page (3 min)**
   - Enter a VacationInfo: dates, a modest budget, interests like
     `["food", "hiking"]`.
   - Watch the pipeline run:
     - Draft itinerary generated (show raw JSON if asked).
     - ReAct loop THOUGHT/ACTION/OBSERVATION steps streamed to the screen.
     - Final narrative summary rendered as prose.
   - Ask a knowledge-base question ("What's the best time of year to visit
     AgentsVille?") to show RAG retrieval pulling from the uploaded PDF.
   - Thumbs-down one itinerary with a comment containing "too few
     activities" three times in a row (or pre-seed `feedback_store.json`)
     to show `policy_updater.maybe_update_policy()` raising the minimum.

5. **Evaluation (30s)**
   - Run `python -m evaluation.deepeval_metrics` in a terminal, show the
     printed pass/fail report.

6. **Wrap-up (30s)**
   - Point to `docs/engineering_justification.md` for the "why" behind
     each tech choice.
