"""
SecureRAG FastAPI Application Entrypoint.

Handles CORS, router registration, and database / vector store boot-strapping.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import FRONTEND_URL, PORT
from app.database import init_db
from app.vector_db import init_collection
from app.routes.auth import router as auth_router
from app.routes.documents import router as documents_router
from app.routes.chat import router as chat_router
from app.routes.audit import router as audit_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise database tables and Qdrant collection on startup."""
    print("[Startup] Initialising PostgreSQL database tables...")
    init_db()
    print("[Startup] Initialising Qdrant vector database collection...")
    init_collection()
    print("[Startup] Bootstrapping completed successfully.")
    yield


app = FastAPI(
    title="SecureRAG API",
    description="Role-Based Access Control (RBAC) Document Retrieval API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration — include localhost dev + Render production
origins = [
    FRONTEND_URL,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://rbdc-rag.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(audit_router)


@app.get("/")
def root():
    """Service health-check endpoint."""
    return {
        "status": "ok",
        "service": "SecureRAG API",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=True)
