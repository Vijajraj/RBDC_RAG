"""
SecureRAG Auth Routes.

POST /auth/register – create a new user and return a JWT.
POST /auth/login    – verify credentials and return a JWT.
GET  /auth/me       – return the current authenticated user's profile.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.database import get_connection

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    role: str = "engineer"
    department: str = "engineering"
    clearance_level: int = 0


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest):
    """Create a new user account and return a signed JWT."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Check for duplicate email
            cur.execute("SELECT id FROM users WHERE email = %s", (body.email,))
            if cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A user with this email already exists.",
                )

            hashed = hash_password(body.password)
            cur.execute(
                """
                INSERT INTO users (email, password_hash, name, role, department, clearance_level)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, email, name, role, department, clearance_level
                """,
                (body.email, hashed, body.name, body.role, body.department, body.clearance_level),
            )
            user = dict(cur.fetchone())
            user["id"] = str(user["id"])
    finally:
        conn.close()

    token = create_access_token(
        {
            "sub": user["id"],
            "email": user["email"],
            "role": user["role"],
            "department": user["department"],
            "clearance_level": user["clearance_level"],
        }
    )
    return TokenResponse(access_token=token, user=user)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    """Authenticate a user and return a signed JWT."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, email, password_hash, name, role, department, clearance_level "
                "FROM users WHERE email = %s",
                (body.email,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if row is None or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    user = {
        "id": str(row["id"]),
        "email": row["email"],
        "name": row["name"],
        "role": row["role"],
        "department": row["department"],
        "clearance_level": row["clearance_level"],
    }

    token = create_access_token(
        {
            "sub": user["id"],
            "email": user["email"],
            "role": user["role"],
            "department": user["department"],
            "clearance_level": user["clearance_level"],
        }
    )
    return TokenResponse(access_token=token, user=user)


@router.get("/me")
def me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return current_user
