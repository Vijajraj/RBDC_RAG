"""
SecureRAG Configuration Module.

Loads all environment variables from .env using python-dotenv
and exports them as module-level constants.
"""

import os
from dotenv import load_dotenv

# Load .env from the backend/ directory (one level up from app/)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

# ---------- Postgres ----------
DATABASE_URL: str = os.getenv("DATABASE_URL", "")

# ---------- Qdrant ----------
QDRANT_URL: str = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")

# ---------- Groq LLM ----------
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

# ---------- Auth / JWT ----------
JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRATION_HOURS: int = 24

# ---------- Frontend ----------
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

# ---------- Embedding ----------
EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM: int = 384

# ---------- Qdrant Collection ----------
QDRANT_COLLECTION: str = "secure_rag_chunks"

# ---------- Server ----------
PORT: int = int(os.getenv("PORT", "8000"))
