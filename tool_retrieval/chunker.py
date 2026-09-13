"""
tool_retrieval/chunker.py
--------------------------
Splits long documents into overlapping chunks small enough to embed and
retrieve accurately. Uses LangChain's RecursiveCharacterTextSplitter, which
tries to break on paragraph/sentence boundaries before falling back to hard
character cuts.
"""

from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 120


def chunk_documents(
    documents: List[Dict],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[Dict]:
    """Turn [{"source": ..., "text": ...}, ...] into a flat list of chunk
    dicts: [{"source": ..., "chunk_id": int, "text": ...}, ...]."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    for doc in documents:
        pieces = splitter.split_text(doc["text"])
        for i, piece in enumerate(pieces):
            chunks.append({"source": doc["source"], "chunk_id": i, "text": piece})
    return chunks
