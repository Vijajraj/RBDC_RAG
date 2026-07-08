"""
SecureRAG Document Routes.

POST /documents/upload – upload a document (admin only) and run ingestion.
GET  /documents/       – list all documents.
"""

from __future__ import annotations

import os
import tempfile
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.auth import get_current_user
from app.database import get_connection
from app.services.ingestion import ingest_document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    department: str = Form(...),
    sensitivity_level: int = Form(0),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Upload a document for ingestion.  Admin-only endpoint."""
    # Access control: only admins (clearance >= 3) may upload
    if current_user.get("clearance_level", 0) < 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users may upload documents.",
        )

    # Save the uploaded file to a temporary location
    suffix = os.path.splitext(file.filename or "file")[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        content = file.file.read()
        tmp.write(content)
        tmp.close()

        doc = ingest_document(
            file_path=tmp.name,
            title=title,
            department=department,
            sensitivity_level=sensitivity_level,
            uploaded_by_id=current_user["id"],
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {exc}",
        )
    finally:
        # Clean up temp file
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)

    return {"message": "Document uploaded and ingested successfully.", "document": doc}


@router.get("/")
def list_documents(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Return all documents (metadata only)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, title, filename, department, sensitivity_level, "
                "chunk_count, uploaded_by, created_at "
                "FROM documents ORDER BY created_at DESC"
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    documents: List[Dict[str, Any]] = []
    for row in rows:
        doc = dict(row)
        doc["id"] = str(doc["id"])
        if doc.get("uploaded_by"):
            doc["uploaded_by"] = str(doc["uploaded_by"])
        if doc.get("created_at"):
            doc["created_at"] = str(doc["created_at"])
        documents.append(doc)

    return {"documents": documents}
