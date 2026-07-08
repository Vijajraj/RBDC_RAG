"""
SecureRAG Database Module.

Provides psycopg2 connection helper and schema initialisation
using raw SQL (no ORM).
"""

import psycopg2
import psycopg2.extras
from app.config import DATABASE_URL


def get_connection():
    """Return a new psycopg2 connection to the Postgres database.

    The caller is responsible for closing the connection.
    Uses RealDictCursor by default so rows come back as dicts.
    """
    conn = psycopg2.connect(
        DATABASE_URL,
        cursor_factory=psycopg2.extras.RealDictCursor,
    )
    conn.autocommit = True
    return conn


def init_db() -> None:
    """Create application tables if they do not already exist."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'engineer',
                    department TEXT NOT NULL DEFAULT 'engineering',
                    clearance_level INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    title TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    department TEXT NOT NULL,
                    sensitivity_level INTEGER NOT NULL DEFAULT 0,
                    chunk_count INTEGER DEFAULT 0,
                    uploaded_by UUID REFERENCES users(id),
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id),
                    user_email TEXT,
                    user_role TEXT,
                    query TEXT NOT NULL,
                    chunks_retrieved INTEGER DEFAULT 0,
                    chunks_denied INTEGER DEFAULT 0,
                    response_preview TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)

        print("[DB] OK - Tables initialised successfully.")
    except Exception as exc:
        print(f"[DB] ERROR - Error initialising tables: {exc}")
        raise
    finally:
        conn.close()
