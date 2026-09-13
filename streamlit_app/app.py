"""
streamlit_app/app.py
-----------------------
The one Streamlit entrypoint for the whole project, with three simple
pages selected from the sidebar:

  1. Data Ingestion   - upload a knowledge file, optionally push to GCS
  2. Build Index      - chunk + embed (Gemini) + save a local FAISS index
  3. Chat             - talk to the AgentsVille Trip Planner agent

Run with:  streamlit run streamlit_app/app.py
"""

import sys
from pathlib import Path

# Allow running `streamlit run streamlit_app/app.py` from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from datetime import date

import config
from streamlit_app.gcp_utils import upload_file_to_bucket
from tool_retrieval.document_loader import load_all_raw_documents
from tool_retrieval.chunker import chunk_documents
from tool_retrieval.faiss_store import build_index_from_chunks, index_exists
from tool_retrieval.retriever import retrieve_context_as_text
from agent.schemas import VacationInfo
from agent.core_agent import plan_trip
from policy_rlhf.feedback_collector import record_feedback
from policy_rlhf.policy_updater import maybe_update_policy
from safety.guardrails import check_input_safety, validate_vacation_dates, validate_budget

config.ensure_directories()

st.set_page_config(page_title="AgentsVille Trip Planner", page_icon="🧭", layout="wide")

PAGE = st.sidebar.radio(
    "Navigate",
    ["1. Data Ingestion", "2. Build Index", "3. Chat"],
)

# ---------------------------------------------------------------------
# PAGE 1 - Data Ingestion
# ---------------------------------------------------------------------
if PAGE == "1. Data Ingestion":
    st.title("📥 Data Ingestion")
    st.write(
        "Upload a knowledge document (PDF, .txt, or .md) about AgentsVille. "
        "It's saved locally to `knowledge/raw/`, and optionally mirrored to "
        "a GCP Cloud Storage bucket."
    )

    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "txt", "md"])
    push_to_gcp = st.checkbox("Also upload to GCP bucket", value=False)

    if uploaded_file is not None and st.button("Save file"):
        dest_path = config.KNOWLEDGE_RAW_DIR / uploaded_file.name
        config.KNOWLEDGE_RAW_DIR.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"Saved locally to {dest_path}")

        if push_to_gcp:
            status = upload_file_to_bucket(str(dest_path), uploaded_file.name)
            st.info(status)

    st.subheader("Files currently in knowledge/raw/")
    existing = sorted(config.KNOWLEDGE_RAW_DIR.glob("*")) if config.KNOWLEDGE_RAW_DIR.exists() else []
    if existing:
        for f in existing:
            st.write(f"- {f.name}")
    else:
        st.caption("No files yet - upload one above.")

# ---------------------------------------------------------------------
# PAGE 2 - Build Index
# ---------------------------------------------------------------------
elif PAGE == "2. Build Index":
    st.title("🧱 Ingest / Index Creation")
    st.write(
        "Chunks every file in `knowledge/raw/`, embeds each chunk with "
        "Gemini's embedding model, and builds a local FAISS index used by "
        "the chat page's retrieval-augmented answers."
    )

    if index_exists():
        st.success("A FAISS index already exists at knowledge/faiss_index/")
    else:
        st.warning("No FAISS index built yet.")

    if st.button("Build / Rebuild Index"):
        with st.spinner("Loading raw documents..."):
            docs = load_all_raw_documents(config.KNOWLEDGE_RAW_DIR)
        if not docs:
            st.error("No documents found in knowledge/raw/. Upload one on the Ingestion page first.")
        else:
            with st.spinner(f"Chunking {len(docs)} document(s)..."):
                chunks = chunk_documents(docs)
            with st.spinner(f"Embedding {len(chunks)} chunk(s) with Gemini and building FAISS index..."):
                build_index_from_chunks(chunks)
            st.success(f"Index built from {len(chunks)} chunks across {len(docs)} document(s).")

# ---------------------------------------------------------------------
# PAGE 3 - Chat
# ---------------------------------------------------------------------
elif PAGE == "3. Chat":
    st.title("💬 AgentsVille Trip Planner")

    tab_plan, tab_ask = st.tabs(["Plan a trip", "Ask the knowledge base"])

    # --- Trip planning sub-tab ---------------------------------------
    with tab_plan:
        st.write("Fill in your trip details and let the agent build (and self-check) your itinerary.")

        col1, col2 = st.columns(2)
        with col1:
            start = st.date_input("Start date", value=date(2026, 6, 1))
            budget = st.number_input("Total budget (USD)", min_value=1.0, value=500.0, step=10.0)
        with col2:
            end = st.date_input("End date", value=date(2026, 6, 3))
            interests_text = st.text_input("Interests (comma-separated)", value="food, art")

        if st.button("Plan my trip"):
            safe, reason = check_input_safety(interests_text)
            date_ok, date_reason = validate_vacation_dates(start, end)
            budget_ok, budget_reason = validate_budget(budget)

            if not safe:
                st.error(reason)
            elif not date_ok:
                st.error(date_reason)
            elif not budget_ok:
                st.error(budget_reason)
            elif not config.GOOGLE_API_KEY:
                st.error("GOOGLE_API_KEY is not set. Add it to your .env file to call Gemini.")
            else:
                vacation_info = VacationInfo(
                    start_date=start,
                    end_date=end,
                    total_budget=budget,
                    interests=[i.strip() for i in interests_text.split(",") if i.strip()],
                )
                with st.spinner("Drafting, revising, and narrating your itinerary..."):
                    try:
                        result = plan_trip(vacation_info)
                        st.session_state["last_plan"] = result
                    except Exception as e:
                        st.error(f"Something went wrong: {e}")

        if "last_plan" in st.session_state:
            result = st.session_state["last_plan"]
            st.subheader("Your trip")
            st.write(result["narrative"])

            with st.expander("See the structured itinerary (JSON)"):
                st.json(result["travel_plan"].model_dump(mode="json"))

            with st.expander("DeepEval report + cloud log status"):
                st.json(result.get("eval_report", {}))
                st.caption(f"Interaction log: {result.get('interaction_log_upload_status')}")
                st.caption(f"Eval log: {result.get('eval_log_upload_status')}")

            st.subheader("Rate this itinerary")
            colA, colB = st.columns(2)
            comment = st.text_input("Optional comment", key="feedback_comment")
            if colA.button("👍 Helpful"):
                record_feedback(result["narrative"], "up", comment)
                st.success("Thanks for the feedback!")
            if colB.button("👎 Not helpful"):
                record_feedback(result["narrative"], "down", comment)
                changed = maybe_update_policy()
                st.success("Thanks - logged." + (" Policy was auto-adjusted." if changed else ""))

    # --- Knowledge base Q&A sub-tab -----------------------------------
    with tab_ask:
        st.write("Ask a question and get an answer grounded in whatever you uploaded and indexed.")
        question = st.text_input("Your question")
        if st.button("Ask") and question:
            if not index_exists():
                st.warning("No index built yet - go to '2. Build Index' first.")
            else:
                context = retrieve_context_as_text(question)
                st.subheader("Retrieved context")
                st.code(context)
                st.caption(
                    "In a fuller build this context would be passed straight into an LLM call "
                    "to produce a grounded answer - wire that up in agent/planner.py if you'd like."
                )
