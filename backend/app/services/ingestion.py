"""
SecureRAG Document Ingestion Service.

Extracts text from PDFs (PyMuPDF), chunks it, embeds with fastembed,
stores metadata in Postgres, and upserts vectors into Qdrant.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF
from fastembed import TextEmbedding

from app.config import EMBEDDING_MODEL
from app.database import get_connection
from app.vector_db import upsert_chunks

# ---------------------------------------------------------------------------
# Embedding model singleton (lazy-loaded)
# ---------------------------------------------------------------------------
_embedding_model: Optional[TextEmbedding] = None


def _get_embedding_model() -> TextEmbedding:
    global _embedding_model
    if _embedding_model is None:
        print(f"[Ingestion] Loading embedding model '{EMBEDDING_MODEL}' ...")
        _embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL)
        print("[Ingestion] OK - Embedding model loaded.")
    return _embedding_model


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------
def extract_text_from_pdf(file_path: str) -> str:
    """Extract all text from a PDF using PyMuPDF."""
    doc = fitz.open(file_path)
    text_parts: List[str] = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts)


def extract_text_from_txt(file_path: str) -> str:
    """Read plain-text files."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_text(file_path: str) -> str:
    """Route to the correct extractor based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in (".txt", ".md", ".text"):
        return extract_text_from_txt(file_path)
    else:
        # Fallback: try reading as plain text
        return extract_text_from_txt(file_path)


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Simple character-based chunking with overlap."""
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - overlap
    return chunks


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------
def embed_chunks(chunks: List[str]) -> List[List[float]]:
    """Return a list of embedding vectors for the given text chunks."""
    model = _get_embedding_model()
    embeddings = list(model.embed(chunks))
    # fastembed returns numpy arrays; convert to plain lists
    return [emb.tolist() for emb in embeddings]


# ---------------------------------------------------------------------------
# Full ingestion pipeline
# ---------------------------------------------------------------------------
def ingest_document(
    file_path: str,
    title: str,
    department: str,
    sensitivity_level: int,
    uploaded_by_id: Optional[str] = None,
) -> Dict[str, Any]:
    """End-to-end ingestion: extract → chunk → embed → store.

    Returns a dict with the saved document metadata.
    """
    # 1. Extract text
    text = extract_text(file_path)
    if not text.strip():
        raise ValueError("No text could be extracted from the document.")

    # 2. Chunk
    chunks = chunk_text(text)
    print(f"[Ingestion] '{title}': {len(chunks)} chunks produced.")

    # 3. Embed
    vectors = embed_chunks(chunks)

    # 4. Save document metadata to Postgres
    filename = os.path.basename(file_path)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO documents (title, filename, department, sensitivity_level, uploaded_by)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, title, filename, department, sensitivity_level, chunk_count, created_at
                """,
                (title, filename, department, sensitivity_level, uploaded_by_id),
            )
            doc = dict(cur.fetchone())
            doc_id = str(doc["id"])
    finally:
        conn.close()

    # 5. Upsert chunks to Qdrant
    qdrant_chunks = [
        {
            "vector": vectors[i],
            "text": chunks[i],
            "document_id": doc_id,
            "department": department,
            "sensitivity_level": sensitivity_level,
            "chunk_index": i,
        }
        for i in range(len(chunks))
    ]
    upsert_chunks(qdrant_chunks)

    # 6. Update chunk_count in Postgres
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE documents SET chunk_count = %s WHERE id = %s",
                (len(chunks), doc_id),
            )
    finally:
        conn.close()

    doc["id"] = doc_id
    doc["chunk_count"] = len(chunks)
    # Ensure created_at is serialisable
    if doc.get("created_at"):
        doc["created_at"] = str(doc["created_at"])

    print(f"[Ingestion] OK - Document '{title}' ingested ({len(chunks)} chunks).")
    return doc
