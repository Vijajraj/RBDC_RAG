"""
SecureRAG Evaluation: Access Correctness Matrix.

A parametrized pytest suite that tests every user x document pair,
verifies authorized vs blocked retrieval, and prints a final result table.
"""

import sys
import os
import pytest
from typing import List

# Ensure backend root is in import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rbac import User, retrieve_authorized_chunks

# Access Matrix Parametrization Data
# Format: (user_email, doc_title, query, expected_success)
MATRIX_DATA = [
    # Engineer (engineering, clearance 1)
    ("eval_engineer@securerag.com", "doc_engineering", "Engineering Operations Handbook coding guidelines", True),
    ("eval_engineer@securerag.com", "doc_hr_policy", "HR Policy General Benefits Overview", False),
    ("eval_engineer@securerag.com", "doc_legal_contract", "Client Contract liability caps", False),
    ("eval_engineer@securerag.com", "doc_finance_q1", "revenue performance cloud hosting costs", False),
    
    # Manager (engineering, clearance 2)
    ("eval_manager@securerag.com", "doc_engineering", "Engineering Operations Handbook coding guidelines", True),
    # Manager has access to overridden salary bands chunk (dept=all, sensitivity 2) inside doc_hr_policy
    ("eval_manager@securerag.com", "doc_hr_policy", "HR Policy General salary bands", True),
    ("eval_manager@securerag.com", "doc_legal_contract", "Client Contract liability caps", False),
    ("eval_manager@securerag.com", "doc_finance_q1", "revenue performance cloud hosting costs", False),

    # HR Admin (hr, clearance 2)
    ("eval_hr_admin@securerag.com", "doc_engineering", "Engineering Operations Handbook coding guidelines", False),
    ("eval_hr_admin@securerag.com", "doc_hr_policy", "HR Policy General Benefits Overview", True),
    ("eval_hr_admin@securerag.com", "doc_legal_contract", "Client Contract liability caps", False),
    ("eval_hr_admin@securerag.com", "doc_finance_q1", "revenue performance cloud hosting costs", False),

    # Admin (admin, clearance 3)
    ("eval_admin@securerag.com", "doc_engineering", "Engineering Operations Handbook coding guidelines", True),
    ("eval_admin@securerag.com", "doc_hr_policy", "HR Policy General Benefits Overview", True),
    ("eval_admin@securerag.com", "doc_legal_contract", "Client Contract liability caps", True),
    ("eval_admin@securerag.com", "doc_finance_q1", "revenue performance cloud hosting costs", True),
]

# Ensure global list in pytest
if not hasattr(pytest, "access_matrix_results"):
    pytest.access_matrix_results = []



def get_user_from_db(email: str) -> User:
    """Helper to fetch user attributes from database by email."""
    from app.database import get_connection
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, role, department, clearance_level FROM users WHERE email = %s",
                (email,)
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"User {email} not found in database.")
            return User(
                id=str(row["id"]),
                role=row["role"],
                department=row["department"],
                clearance_level=row["clearance_level"]
            )
    finally:
        conn.close()


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


@pytest.mark.parametrize("user_email, doc_title, query, expected_success", MATRIX_DATA)
def test_access_correctness_matrix(user_email, doc_title, query, expected_success):
    """Assert whether retrieval should succeed (return chunks) or fail closed (0 chunks)."""
    user = get_user_from_db(user_email)
    result = retrieve_authorized_chunks(query=query, user=user)
    
    # Check if we successfully retrieved any chunk belonging to the target document
    target_doc_id = get_doc_id_from_db(doc_title)
    matching_chunks = [c for c in result.chunks if c.document_id == target_doc_id]
    retrieved_count = len(matching_chunks)
    
    success = (retrieved_count > 0) == expected_success
    
    # Store results for printout
    pytest.access_matrix_results.append({
        "user": user_email.split("@")[0].replace("eval_", ""),
        "doc": doc_title,
        "expected": "Allowed" if expected_success else "Blocked",
        "actual": "Allowed" if retrieved_count > 0 else "Blocked",
        "chunks": retrieved_count,
        "passed": "PASS" if success else "FAIL"
    })
    
    if expected_success:
        assert retrieved_count > 0, f"Expected access to {doc_title} for {user_email}, but retrieved 0 chunks."
    else:
        assert retrieved_count == 0, f"Expected blocked access to {doc_title} for {user_email}, but retrieved {retrieved_count} chunks."

