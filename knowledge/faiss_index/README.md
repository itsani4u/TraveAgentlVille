This folder holds the generated FAISS index (index.faiss + index.pkl).

It starts empty. Build it via the "2. Build Index" page in the Streamlit
app, or by calling tool_retrieval.faiss_store.build_index_from_chunks()
directly. These files are git-ignored since they're regenerated output,
not source content.
