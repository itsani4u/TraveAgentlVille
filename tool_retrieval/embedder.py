"""
tool_retrieval/embedder.py
----------------------------
Wraps Gemini's embedding model behind one function so the rest of the app
never has to think about which embedding provider is in use.
"""

from langchain_google_genai import GoogleGenerativeAIEmbeddings
import config


def get_embedder() -> GoogleGenerativeAIEmbeddings:
    """Return a LangChain-compatible Gemini embeddings object."""
    return GoogleGenerativeAIEmbeddings(
        model=config.GEMINI_EMBEDDING_MODEL,
        google_api_key=config.GOOGLE_API_KEY,
    )
