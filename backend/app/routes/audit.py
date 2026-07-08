"""
SecureRAG Audit Routes.

GET /audit/logs – return recent audit log entries (admin only).
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_user
from app.database import get_connection

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs")
def get_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Return the most recent audit log entries.  Admin-only."""
    if current_user.get("clearance_level", 0) < 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users may view audit logs.",
        )

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, user_email, user_role, query,
                       chunks_retrieved, chunks_denied, response_preview, created_at
                FROM audit_logs
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    logs: List[Dict[str, Any]] = []
    for row in rows:
        log = dict(row)
        log["id"] = str(log["id"])
        if log.get("user_id"):
            log["user_id"] = str(log["user_id"])
        if log.get("created_at"):
            log["created_at"] = str(log["created_at"])
        logs.append(log)

    return {"logs": logs, "count": len(logs)}
