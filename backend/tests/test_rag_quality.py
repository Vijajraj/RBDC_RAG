"""
SecureRAG Evaluation: RAG Quality and Grounding.

Tests 12 distinct questions across the seeded document catalog.
Verifies relevance (retrieved correct chunk) and grounding (LLM contains correct details).
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is in import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
client = TestClient(app)

# Quality Evaluation dataset
# Format: (question, expected_doc_title, expected_answer_keyword)
QUALITY_TESTS = [
    # 1. doc_engineering
    ("What guidelines are listed in the Engineering Operations Handbook?", "doc_engineering", "modular"),
    ("When do CI/CD deployments run automatically?", "doc_engineering", "merged"),
    ("What processes should all engineers follow in doc_engineering?", "doc_engineering", "peer review"),
    
    # 2. doc_hr_policy
    ("What are the core working hours at SecureRAG in doc_hr_policy?", "doc_hr_policy", "10 am to 4 pm"),
    ("What percentage pension matching is offered to personnel in doc_hr_policy?", "doc_hr_policy", "4%"),
    ("What is the base salary range for L3 Senior Engineers in doc_hr_policy?", "doc_hr_policy", "$115,000"),
    
    # 3. doc_legal_contract
    ("What is the total annual value of the service contract with Client X in doc_legal_contract?", "doc_legal_contract", "$450,000"),
    ("Under what state's jurisdiction will contract disputes be resolved in doc_legal_contract?", "doc_legal_contract", "california"),
    ("What proprietary clauses are detailed in the licensing agreement of doc_legal_contract?", "doc_legal_contract", "intellectual property"),
    
    # 4. doc_finance_q1
    ("What was the total revenue recorded by SecureRAG in Q1 in doc_finance_q1?", "doc_finance_q1", "$1.85m"),
    ("What post-money valuation is targeted for the Series A funding round in doc_finance_q1?", "doc_finance_q1", "$40,000,000"),
    ("How many months of runway do current cash reserves provide in doc_finance_q1?", "doc_finance_q1", "18 months"),
]

# Ensure global list in pytest
if not hasattr(pytest, "rag_quality_results"):
    pytest.rag_quality_results = []



def get_auth_headers(email: str) -> dict:
    """Helper to authenticate admin user."""
    resp = client.post("/auth/login", json={"email": email, "password": "password123"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def get_doc_id_from_db(title: str) -> str:
    """Helper to fetch document ID by title from Postgres."""
    from app.database import get_connection
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM documents WHERE title = %s", (title,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Document {title} not found in database.")
            return str(row["id"])
    finally:
        conn.close()


@pytest.mark.parametrize("question, doc_title, answer_keyword", QUALITY_TESTS)
def test_rag_quality_and_grounding(question, doc_title, answer_keyword):
    """Run RAG query as Admin and verify relevance and grounding."""
    headers = get_auth_headers("eval_admin@securerag.com")
    resp = client.post("/chat/ask", json={"question": question}, headers=headers)
    assert resp.status_code == 200
    
    data = resp.json()
    retrieved = data["chunks_retrieved"]
    answer = data["answer"].lower()
    
    # Verify relevance: check if the correct document chunk was retrieved by its database ID
    target_doc_id = get_doc_id_from_db(doc_title)
    correct_chunk_retrieved = any(chunk["document_id"] == target_doc_id for chunk in retrieved)
    
    # Verify grounding: check if the LLM's final answer contains the expected grounded facts
    answer_grounded = answer_keyword.lower() in answer
    
    # Record metrics for report
    pytest.rag_quality_results.append({
        "question": question[:40] + "...",
        "doc": doc_title,
        "relevance": "YES" if correct_chunk_retrieved else "NO",
        "grounding": "YES" if answer_grounded else "NO",
        "passed": "PASS" if (correct_chunk_retrieved and answer_grounded) else "FAIL"
    })
    
    assert correct_chunk_retrieved, f"Relevance check failed: target document '{doc_title}' ({target_doc_id}) chunk was not retrieved."
    assert answer_grounded, f"Grounding check failed: LLM answer did not contain fact '{answer_keyword}'."

