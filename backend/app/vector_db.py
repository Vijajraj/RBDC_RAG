"""
SecureRAG Vector Database Module.

Wraps qdrant-client for collection management, upserting chunks,
and filtered similarity search.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    Range,
    VectorParams,
    PayloadSchemaType,
)

from app.config import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION, EMBEDDING_DIM

# ---------------------------------------------------------------------------
# Client singleton
# ---------------------------------------------------------------------------
_client: Optional[QdrantClient] = None


def _get_client() -> QdrantClient:
    """Lazy-initialise and return the Qdrant client singleton."""
    global _client
    if _client is None:
        _client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            timeout=30,
        )
    return _client


# ---------------------------------------------------------------------------
# Collection bootstrap
# ---------------------------------------------------------------------------
def init_collection() -> None:
    """Create the vector collection if it does not already exist."""
    client = _get_client()
    collections = [c.name for c in client.get_collections().collections]
    if QDRANT_COLLECTION not in collections:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=EMBEDDING_DIM,
                distance=Distance.COSINE,
            ),
        )
        print(f"[Qdrant] OK - Created collection '{QDRANT_COLLECTION}'.")
    else:
        print(f"[Qdrant] OK - Collection '{QDRANT_COLLECTION}' already exists.")

    # Create payload indices to support filtered range queries
    try:
        client.create_payload_index(
            collection_name=QDRANT_COLLECTION,
            field_name="sensitivity_level",
            field_schema=PayloadSchemaType.INTEGER,
        )
        client.create_payload_index(
            collection_name=QDRANT_COLLECTION,
            field_name="department",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        print("[Qdrant] OK - Created payload indexes for sensitivity_level and department.")
    except Exception as e:
        print(f"[Qdrant] Warning - Failed to create payload indexes: {e}")


# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------
def upsert_chunks(chunks: List[Dict[str, Any]]) -> None:
    """Upsert a batch of chunk points into Qdrant.

    Each item in *chunks* must contain:
        vector       – list[float]
        text         – str
        document_id  – str (UUID)
        department   – str
        sensitivity_level – int
        chunk_index  – int
    """
    client = _get_client()
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=chunk["vector"],
            payload={
                "text": chunk["text"],
                "document_id": chunk["document_id"],
                "department": chunk["department"],
                "sensitivity_level": chunk["sensitivity_level"],
                "chunk_index": chunk["chunk_index"],
            },
        )
        for chunk in chunks
    ]
    client.upsert(collection_name=QDRANT_COLLECTION, points=points)


# ---------------------------------------------------------------------------
# Filtered search (respects RBAC)
# ---------------------------------------------------------------------------
def search_with_filter(
    query_vector: List[float],
    department: str,
    clearance_level: int,
    limit: int = 5,
) -> list:
    """Search Qdrant with RBAC-aware filters.

    • Admin (clearance_level >= 3): only sensitivity_level <= clearance_level
    • Others: (department matches OR department == 'all')
              AND sensitivity_level <= clearance_level
    """
    client = _get_client()

    sensitivity_condition = FieldCondition(
        key="sensitivity_level",
        range=Range(lte=clearance_level),
    )

    if clearance_level >= 3:
        # Admins can see everything up to their sensitivity ceiling
        query_filter = Filter(must=[sensitivity_condition])
    else:
        # Non-admins: restrict to own department + "all"
        dept_filter = Filter(
            should=[
                FieldCondition(key="department", match=MatchValue(value=department)),
                FieldCondition(key="department", match=MatchValue(value="all")),
            ]
        )
        query_filter = Filter(
            must=[
                sensitivity_condition,
                dept_filter,
            ]
        )

    response = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        query_filter=query_filter,
        limit=limit,
    )
    return response.points


# ---------------------------------------------------------------------------
# Unfiltered search (for calculating denied count)
# ---------------------------------------------------------------------------
def get_all_chunks_count_by_query(
    query_vector: List[float],
    limit: int = 20,
) -> list:
    """Search WITHOUT any RBAC filter so we can compute how many chunks
    the user was *denied* access to."""
    client = _get_client()
    response = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        limit=limit,
    )
    return response.points
