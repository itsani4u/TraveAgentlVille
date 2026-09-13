"""
tool_retrieval/document_loader.py
----------------------------------
Loads raw knowledge files (PDF or text) from knowledge/raw/ into plain
Python strings, ready for chunking. Kept deliberately simple: one function,
one job.
"""

from pathlib import Path
from typing import List
from pypdf import PdfReader


def load_pdf(pdf_path: Path) -> str:
    """Extract all text from a PDF file as one big string."""
    reader = PdfReader(str(pdf_path))
    pages_text = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages_text)


def load_text(text_path: Path) -> str:
    """Load a plain .txt/.md file as a string."""
    return Path(text_path).read_text(encoding="utf-8", errors="ignore")


def load_all_raw_documents(raw_dir: Path) -> List[dict]:
    """Load every supported file in knowledge/raw/ into a list of
    {"source": filename, "text": content} dicts."""
    documents = []
    for path in sorted(Path(raw_dir).glob("*")):
        if path.suffix.lower() == ".pdf":
            text = load_pdf(path)
        elif path.suffix.lower() in (".txt", ".md"):
            text = load_text(path)
        else:
            continue
        if text.strip():
            documents.append({"source": path.name, "text": text})
    return documents
