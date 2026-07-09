"""
SecureRAG Chat / RAG Routes.

POST /chat/ask – answer a question using RBAC-filtered retrieval + Groq LLM.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth import get_current_user
from app.database import get_connection
from app.services.llm import generate_answer
from app.rbac import User as RBACUser, retrieve_authorized_chunks

router = APIRouter(prefix="/chat", tags=["chat"])


class AskRequest(BaseModel):
    """Pydantic model representing RAG chat request."""
    question: str


@router.post("/ask")
def ask(body: AskRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Answer a question through the secure RAG pipeline.

    1. Enforce Server-Side Roles: Build User model from Postgres-derived current_user.
    2. Retrieve Authorized Chunks: Employs secure pre-filtering at Qdrant layer.
    3. Generate response using Groq LLM.
    4. Log audit trace and denial reasons transactionally.
    """
    question = body.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question must not be empty.",
        )

    # 1. Enforce Server-Side Roles: Instantiate RBACUser model strictly from DB record
    user_profile = RBACUser(
        id=current_user["id"],
        role=current_user["role"],
        department=current_user["department"],
        clearance_level=current_user["clearance_level"]
    )

    # 2. Retrieve Authorized Chunks (pre-filtering is enforced within Qdrant itself)
    retrieval = retrieve_authorized_chunks(query=question, user=user_profile, limit=5)

    # Build LLM context from allowed chunks
    context_chunks = [c.text for c in retrieval.chunks]

    # Convert Pydantic Chunk objects to dicts for API response compatibility
    retrieval_info = [
        {
            "text": chunk.text,
            "document_id": chunk.document_id,
            "score": chunk.score,
            "department": chunk.department,
            "sensitivity_level": chunk.sensitivity_level,
        }
        for chunk in retrieval.chunks
    ]

    # 3. Call LLM
    role_info = {
        "role": user_profile.role,
        "department": user_profile.department,
        "clearance_level": user_profile.clearance_level,
    }
    answer = generate_answer(query=question, context_chunks=context_chunks, role_info=role_info)

    # 4. Log Audit Trace Transactionally
    response_preview = answer[:200] if answer else ""
    
    conn = get_connection()
    conn.autocommit = False  # Enable transaction block
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO audit_logs (
                    user_id, user_email, user_role, query,
                    chunks_retrieved, chunks_denied, denial_reason, response_preview
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_profile.id,
                    current_user["email"],
                    user_profile.role,
                    question,
                    len(retrieval.chunks),
                    retrieval.excluded_count,
                    retrieval.denial_reason,
                    response_preview,
                ),
            )
        conn.commit()  # Commit transaction atomically
    except Exception as exc:
        conn.rollback()  # Rollback on database failure
        print(f"[Audit Log] Transaction rolled back due to error: {exc}")
    finally:
        conn.close()

    # 5. Response
    return {
        "answer": answer,
        "chunks_retrieved": retrieval_info,
        "chunks_denied_count": retrieval.excluded_count,
        "total_chunks_found": len(retrieval.chunks) + retrieval.excluded_count,
        "denial_reason": retrieval.denial_reason,
    }
