"""
config.py
---------
One place for every setting the project needs. Student-friendly on purpose:
plain variables loaded from environment variables, with sane defaults.

Everything else in the project imports from here instead of calling
os.getenv() everywhere.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load variables from a local .env file (if present) into the environment.
load_dotenv()

# --- Project paths -----------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

KNOWLEDGE_RAW_DIR = BASE_DIR / "knowledge" / "raw"
KNOWLEDGE_PROCESSED_DIR = BASE_DIR / "knowledge" / "processed"
FAISS_INDEX_DIR = BASE_DIR / "knowledge" / "faiss_index"

DATA_POLICY_PATH = BASE_DIR / "data" / "policy" / "policy.json"
DATA_RLHF_PATH = BASE_DIR / "data" / "rlhf" / "feedback_store.json"
DATA_EVAL_RUBRIC_PATH = BASE_DIR / "data" / "evaluation" / "eval_rubric.json"

LOGS_DIR = BASE_DIR / "logs"

# --- Gemini (LLM + embeddings) -----------------------------------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_LLM_MODEL = os.getenv("GEMINI_LLM_MODEL", "gemini-1.5-flash")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004")

# --- Agent behaviour -----------------------------------------------------
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
MAX_REACT_STEPS = int(os.getenv("MAX_REACT_STEPS", "6"))

# --- GCP -----------------------------------------------------------------
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME", "agentsville-knowledge-bucket")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")

# --- Logging ---------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def ensure_directories() -> None:
    """Create every folder the app expects to write into, if missing."""
    for d in [
        KNOWLEDGE_RAW_DIR,
        KNOWLEDGE_PROCESSED_DIR,
        FAISS_INDEX_DIR,
        DATA_POLICY_PATH.parent,
        DATA_RLHF_PATH.parent,
        DATA_EVAL_RUBRIC_PATH.parent,
        LOGS_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)
