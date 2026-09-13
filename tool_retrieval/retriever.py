"""
tool_retrieval/retriever.py
------------------------------
Thin convenience layer on top of the FAISS index: "give me the top-k
knowledge chunks relevant to this query" as plain text, ready to paste into
a prompt.
"""

from typing import List
from tool_retrieval.faiss_store import load_index, index_exists


def retrieve_context(query: str, k: int = 4) -> List[str]:
    """Return the top-k most relevant knowledge chunks for a query.
    Returns an empty list if no index has been built yet."""
    if not index_exists():
        return []
    vector_store = load_index()
    results = vector_store.similarity_search(query, k=k)
    return [doc.page_content for doc in results]


def retrieve_context_as_text(query: str, k: int = 4) -> str:
    """Same as retrieve_context, joined into one string for prompt-stuffing."""
    chunks = retrieve_context(query, k=k)
    if not chunks:
        return "(no knowledge base results found)"
    return "\n---\n".join(chunks)
