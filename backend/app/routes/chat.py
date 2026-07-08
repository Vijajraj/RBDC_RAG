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
from app.services.ingestion import embed_chunks
from app.services.llm import generate_answer
from app.vector_db import get_all_chunks_count_by_query, search_with_filter

router = APIRouter(prefix="/chat", tags=["chat"])


class AskRequest(BaseModel):
    question: str


@router.post("/ask")
def ask(body: AskRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Answer a question through the secure RAG pipeline.

    1. Embed the question.
    2. Search Qdrant WITH RBAC filter → filtered results.
    3. Search Qdrant WITHOUT filter → total results (for denied count).
    4. Build context from filtered results.
    5. Call Groq LLM.
    6. Log to audit_logs.
    7. Return the answer + retrieval metadata.
    """
    question = body.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question must not be empty.",
        )

    # 1. Embed the question (embed_chunks expects a list)
    vectors = embed_chunks([question])
    query_vector = vectors[0]

    # 2. Filtered search (RBAC)
    filtered_results = search_with_filter(
        query_vector=query_vector,
        department=current_user["department"],
        clearance_level=current_user["clearance_level"],
        limit=5,
    )

    # 3. Unfiltered search (total matches)
    all_results = get_all_chunks_count_by_query(query_vector=query_vector, limit=20)
    total_chunks_found = len(all_results)
    chunks_retrieved = len(filtered_results)
    chunks_denied = max(0, total_chunks_found - chunks_retrieved)

    # 4. Build context
    context_chunks: List[str] = []
    retrieval_info: List[Dict[str, Any]] = []
    for hit in filtered_results:
        text = hit.payload.get("text", "")
        context_chunks.append(text)
        retrieval_info.append(
            {
                "text": text,
                "document_id": hit.payload.get("document_id"),
                "score": round(hit.score, 4),
            }
        )

    # 5. Call LLM
    role_info = {
        "role": current_user["role"],
        "department": current_user["department"],
        "clearance_level": current_user["clearance_level"],
    }
    answer = generate_answer(query=question, context_chunks=context_chunks, role_info=role_info)

    # 6. Audit log
    response_preview = answer[:200] if answer else ""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO audit_logs (user_id, user_email, user_role, query,
                                        chunks_retrieved, chunks_denied, response_preview)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    current_user["id"],
                    current_user["email"],
                    current_user["role"],
                    question,
                    chunks_retrieved,
                    chunks_denied,
                    response_preview,
                ),
            )
    finally:
        conn.close()

    # 7. Response
    return {
        "answer": answer,
        "chunks_retrieved": retrieval_info,
        "chunks_denied_count": chunks_denied,
        "total_chunks_found": total_chunks_found,
    }
