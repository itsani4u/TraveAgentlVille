"""
tool_retrieval/faiss_store.py
-------------------------------
Build, save, and load a local FAISS vector index built from knowledge
chunks + Gemini embeddings.

Files land in knowledge/faiss_index/ as index.faiss + index.pkl, matching
the project layout.
"""

import json
from pathlib import Path
from typing import List, Dict

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from tool_retrieval.embedder import get_embedder
import config


def build_index_from_chunks(chunks: List[Dict], save_dir: Path = config.FAISS_INDEX_DIR) -> FAISS:
    """Embed every chunk with Gemini and build/save a FAISS index."""
    docs = [
        Document(page_content=c["text"], metadata={"source": c["source"], "chunk_id": c["chunk_id"]})
        for c in chunks
    ]
    embedder = get_embedder()
    vector_store = FAISS.from_documents(docs, embedder)

    save_dir.mkdir(parents=True, exist_ok=True)
    vector_store.save_local(str(save_dir))

    # Also keep a human-readable copy of the chunks for debugging.
    (config.KNOWLEDGE_PROCESSED_DIR).mkdir(parents=True, exist_ok=True)
    (config.KNOWLEDGE_PROCESSED_DIR / "chunks.json").write_text(json.dumps(chunks, indent=2))

    return vector_store


def load_index(save_dir: Path = config.FAISS_INDEX_DIR) -> FAISS:
    """Load a previously built FAISS index from disk."""
    embedder = get_embedder()
    return FAISS.load_local(str(save_dir), embedder, allow_dangerous_deserialization=True)


def index_exists(save_dir: Path = config.FAISS_INDEX_DIR) -> bool:
    return (save_dir / "index.faiss").exists() and (save_dir / "index.pkl").exists()
