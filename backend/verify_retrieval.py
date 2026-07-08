"""
SecureRAG Retrieval and RBAC Verification Script.

Tests the Qdrant filtering logic across different roles and clearance levels
directly without starting the HTTP server.
"""

import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ingestion import embed_chunks
from app.vector_db import search_with_filter, get_all_chunks_count_by_query
from app.database import get_connection

TEST_PROMPT = "what is the salary band for L4?"

USERS = {
    "alice": {
        "name": "Alice Smith (Engineer)",
        "role": "engineer",
        "department": "engineering",
        "clearance_level": 0,
    },
    "bob": {
        "name": "Bob Jones (Manager)",
        "role": "manager",
        "department": "engineering",
        "clearance_level": 1,
    },
    "carol": {
        "name": "Carol Vance (HR)",
        "role": "hr",
        "department": "hr",
        "clearance_level": 2,
    },
    "admin": {
        "name": "Super Admin (Admin)",
        "role": "admin",
        "department": "admin",
        "clearance_level": 3,
    },
}


def verify_rbac_retrieval():
    print("=== SecureRAG RBAC Verification ===")
    print(f"Generating query embedding for: '{TEST_PROMPT}'\n")

    # Generate query vector
    query_vector = embed_chunks([TEST_PROMPT])[0]

    # Verify database contents
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, department, sensitivity_level FROM documents")
            docs = cur.fetchall()
            print("--- Document Registry in Postgres ---")
            for doc in docs:
                print(f"ID: {doc['id']} | Title: {doc['title']} | Dept: {doc['department']} | Clearance: L{doc['sensitivity_level']}")
            print("-" * 38 + "\n")
    finally:
        conn.close()

    # Perform unfiltered search to see the baseline matches
    print("--- Unfiltered Search (Baseline Candidate Set) ---")
    unfiltered_hits = get_all_chunks_count_by_query(query_vector, limit=5)
    for i, hit in enumerate(unfiltered_hits):
        payload = hit.payload
        print(f"Hit #{i+1}: Score: {hit.score:.4f} | Title: {payload.get('text')[:30]}... | Dept: {payload.get('department')} | Sensitivity: L{payload.get('sensitivity_level')}")
    print("-" * 50 + "\n")

    # Run tests for each user profile
    for username, profile in USERS.items():
        print(f"Testing retrieval for: {profile['name']}")
        print(f"Clearance: Level {profile['clearance_level']} | Department: {profile['department']}")

        # Query Qdrant with filters
        hits = search_with_filter(
            query_vector=query_vector,
            department=profile["department"],
            clearance_level=profile["clearance_level"],
            limit=5
        )

        print(f"-> Chunks retrieved: {len(hits)}")
        
        # Check if they retrieved any restricted contents
        denied_retrieved = 0
        for i, hit in enumerate(hits):
            payload = hit.payload
            doc_dept = payload.get("department")
            doc_level = payload.get("sensitivity_level")
            
            # Check violation
            violates_dept = (profile["clearance_level"] < 3) and (doc_dept != "all") and (doc_dept != profile["department"])
            violates_level = doc_level > profile["clearance_level"]
            
            status = "OK"
            if violates_dept or violates_level:
                status = "!!! LEAK VIOLATION !!!"
                denied_retrieved += 1
                
            print(f"   [{status}] Hit #{i+1}: {payload.get('text')[:40]}... (Dept: {doc_dept}, Sensitivity: L{doc_level})")

        if denied_retrieved > 0:
            print(f"[FAIL] TEST FAILED: User {username} bypassed RBAC policies!\n")
        else:
            print(f"[PASS] TEST PASSED: Access control fully enforced for {username}.\n")

    print("=== Verification Completed ===")


if __name__ == "__main__":
    verify_rbac_retrieval()
