"""
SecureRAG RBAC and Retrieval Filter Module.

This is the security-critical core of the system. It builds Qdrant pre-filters,
performs authorized retrieval, and compiles access audit logs.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from qdrant_client.http.models import (
    Filter,
    FieldCondition,
    Range,
    MatchValue,
    IsEmptyCondition,
    PayloadField
)

from app.config import QDRANT_COLLECTION
from app.vector_db import _get_client
from app.services.ingestion import embed_chunks


class User(BaseModel):
    """Pydantic model representing user identity and credentials.
    
    Clearance level mapping:
    0 = Public
    1 = Internal
    2 = Confidential
    3 = Restricted
    """
    id: Optional[str] = None
    role: str
    department: Optional[str] = None
    clearance_level: Optional[int] = None


class Chunk(BaseModel):
    """Pydantic model representing a retrieved document chunk."""
    text: str
    document_id: str
    score: float
    department: str
    sensitivity_level: int
    chunk_index: int


class RetrievalResult(BaseModel):
    """Pydantic model containing the retrieval results and access audit trace."""
    chunks: List[Chunk]
    excluded_count: int
    denial_reason: Optional[str] = None


def build_qdrant_filter(user: User) -> Filter:
    """Pure, unit-testable function to build a secure Qdrant filter based on user RBAC profile.

    Enforces:
      1. FAIL CLOSED: If clearance_level or department is missing (non-admin),
         returns an impossible filter (sensitivity_level < 0) ensuring zero results.
      2. EXCLUDE MISSING METADATA: Any chunk missing department or sensitivity_level
         payload parameters is explicitly filtered out.
      3. CORRECT BOOLEAN LOGIC: A chunk must pass both:
         - sensitivity_level <= user.clearance_level AND
         - (department == user.department OR department == 'all' OR user.role == 'admin')
    """
    # 1. Fail Closed - Unset clearance level yields zero results
    if user.clearance_level is None:
        # Impossible range query serving as a zero-match filter
        return Filter(must=[FieldCondition(key="sensitivity_level", range=Range(lt=0))])

    # 2. Exclude missing metadata (must_not contain empty fields)
    must_not_conditions = [
        IsEmptyCondition(is_empty=PayloadField(key="department")),
        IsEmptyCondition(is_empty=PayloadField(key="sensitivity_level"))
    ]

    # Sensitivity range ceiling condition
    sensitivity_condition = FieldCondition(
        key="sensitivity_level",
        range=Range(lte=user.clearance_level)
    )

    # 3. Correct Boolean Logic: AND combined with OR
    if user.role == "admin":
        # Admin is not bound by department boundary check
        return Filter(
            must=[sensitivity_condition],
            must_not=must_not_conditions
        )
    else:
        # Non-admins: fail closed if department is missing
        if not user.department:
            return Filter(must=[FieldCondition(key="sensitivity_level", range=Range(lt=0))])

        dept_condition = Filter(
            should=[
                FieldCondition(key="department", match=MatchValue(value=user.department)),
                FieldCondition(key="department", match=MatchValue(value="all"))
            ]
        )

        return Filter(
            must=[
                sensitivity_condition,
                dept_condition
            ],
            must_not=must_not_conditions
        )


def retrieve_authorized_chunks(query: str, user: User, limit: int = 5) -> RetrievalResult:
    """Retrieve authorized document chunks with secure pre-filtering and build audit trace.
    
    1. Filter before retrieval: Generates the filter and queries Qdrant directly.
    2. Exclude details trace: Compares results to a broader query to log denied access reasons.
    """
    # Embed query string to obtain search vector
    vectors = embed_chunks([query])
    query_vector = vectors[0]

    client = _get_client()

    # 1. Fetch authorized chunks using secure pre-filter
    auth_filter = build_qdrant_filter(user)
    auth_response = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        query_filter=auth_filter,
        limit=limit
    )

    # Convert to Pydantic Chunk objects
    allowed_chunks: List[Chunk] = []
    for hit in auth_response.points:
        allowed_chunks.append(
            Chunk(
                text=hit.payload.get("text", ""),
                document_id=hit.payload.get("document_id", ""),
                score=round(hit.score, 4),
                department=hit.payload.get("department", ""),
                sensitivity_level=hit.payload.get("sensitivity_level", 0),
                chunk_index=hit.payload.get("chunk_index", 0)
            )
        )

    # 2. Fetch unfiltered candidate chunks to identify denied matches
    unfiltered_response = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        limit=20
    )

    # Find which chunks from the top candidates were denied
    allowed_ids = {hit.payload.get("chunk_index") for hit in auth_response.points}
    denied_reasons: List[str] = []
    excluded_count = 0

    # We do NOT filter results in Python to determine the allowed set (Requirement 1).
    # Python is strictly used to evaluate and report audit logs on top-k candidates.
    for hit in unfiltered_response.points:
        chunk_idx = hit.payload.get("chunk_index")
        if chunk_idx not in allowed_ids:
            # Chunk was candidate but got filtered out by Qdrant
            excluded_count += 1
            
            # Determine why this candidate was excluded
            chunk_dept = hit.payload.get("department")
            chunk_sens = hit.payload.get("sensitivity_level")

            if chunk_sens is None or chunk_dept is None:
                denied_reasons.append("missing metadata")
            elif user.clearance_level is None or chunk_sens > user.clearance_level:
                denied_reasons.append(
                    f"insufficient clearance (required L{chunk_sens}, user has L{user.clearance_level or 0})"
                )
            elif user.role != "admin" and chunk_dept != user.department and chunk_dept != "all":
                denied_reasons.append(
                    f"department mismatch (chunk={chunk_dept}, user={user.department})"
                )

    # Compile the final denial reasons trace
    denial_reason = None
    if denied_reasons:
        # De-duplicate reasons while preserving order
        unique_reasons = []
        for r in denied_reasons:
            if r not in unique_reasons:
                unique_reasons.append(r)
        denial_reason = f"{excluded_count} candidate chunks excluded: " + ", ".join(unique_reasons)

    return RetrievalResult(
        chunks=allowed_chunks,
        excluded_count=excluded_count,
        denial_reason=denial_reason
    )
