"""
SecureRAG Evaluation Seeding Script.

Seeds specific documents, users, and missing-metadata chunks to support
the comprehensive RBAC evaluation suite.
"""

import os
import sys
import uuid
import tempfile

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.auth import hash_password
from app.database import get_connection
from app.vector_db import init_collection, _get_client, QDRANT_COLLECTION
from app.services.ingestion import ingest_document, embed_chunks
from qdrant_client.http.models import PointStruct

EVAL_USERS = [
    {
        "email": "eval_engineer@securerag.com",
        "password": "password123",
        "name": "Eval Engineer",
        "role": "engineer",
        "department": "engineering",
        "clearance_level": 1,
    },
    {
        "email": "eval_manager@securerag.com",
        "password": "password123",
        "name": "Eval Manager",
        "role": "manager",
        "department": "engineering",
        "clearance_level": 2,
    },
    {
        "email": "eval_hr_admin@securerag.com",
        "password": "password123",
        "name": "Eval HR Admin",
        "role": "hr",
        "department": "hr",
        "clearance_level": 2,
    },
    {
        "email": "eval_admin@securerag.com",
        "password": "password123",
        "name": "Eval Admin",
        "role": "admin",
        "department": "admin",
        "clearance_level": 3,
    },
]

EVAL_DOCS = [
    {
        "title": "doc_engineering",
        "filename": "doc_engineering.txt",
        "department": "engineering",
        "sensitivity_level": 0,
        "content": """
SecureRAG Engineering Operations Handbook.
This is public engineering information regarding coding guidelines and best practices.
All engineers should write modular code, follow peer review processes, and write tests for every function.
CI/CD deployments run automatically when PRs are merged to main.
        """
    },
    {
        "title": "doc_hr_policy",
        "filename": "doc_hr_policy.txt",
        "department": "hr",
        "sensitivity_level": 1,
        "content": """
SecureRAG HR Policy and General Benefits Overview.
This document outlines standard workplace rules, remote work benefits, and leave policies for all employees.
Section 1: General Work Environment. Standard working hours are flexible but core hours are 10 AM to 4 PM.
Section 2: Salary bands and compensation reviews.
The base salary bands for career levels are restricted: L1 Associate ranges $60k-$80k. L2 Engineer ranges $85k-$110k.
L3 Senior ranges $115k-$145k. L4 Staff ranges $150k-$185k. L5 Principal ranges $190k-$240k.
Section 3: Standard medical coverage and pension matching of 4% are offered to all full-time personnel.
        """
    },
    {
        "title": "doc_legal_contract",
        "filename": "doc_legal_contract.txt",
        "department": "legal",
        "sensitivity_level": 3,
        "content": """
SecureRAG Confidential Client Contract - Legal Department.
This legal contract details proprietary software licensing, intellectual property clauses, and liability caps.
The contract value is $450,000 annually. Disputes shall be resolved under the jurisdiction of California courts.
All materials developed are strictly protected as intellectual property.
        """
    },
    {
        "title": "doc_finance_q1",
        "filename": "doc_finance_q1.txt",
        "department": "finance",
        "sensitivity_level": 2,
        "content": """
SecureRAG Q1 Executive Financial Projections.
This document summarizes revenue performance and capital allocation runway plans.
Revenue for Q1 was $1.85M with operating expenses of $1.2M. Runway is approximately 18 months.
Series A funding round targets $8,000,000 at a post-money valuation of $40,000,000.
        """
    }
]


def seed_eval():
    print("=" * 60)
    print("Seeding SecureRAG Evaluation Data")
    print("=" * 60)

    conn = get_connection()
    client = _get_client()

    # 1. Seed Users
    print("\n1. Seeding Evaluation Users...")
    try:
        with conn.cursor() as cur:
            for user in EVAL_USERS:
                cur.execute("SELECT id FROM users WHERE email = %s", (user["email"],))
                row = cur.fetchone()
                if row:
                    print(f"  User {user['email']} already exists. Skipping.")
                else:
                    hashed = hash_password(user["password"])
                    cur.execute(
                        """
                        INSERT INTO users (email, password_hash, name, role, department, clearance_level)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (user["email"], hashed, user["name"], user["role"], user["department"], user["clearance_level"])
                    )
                    print(f"  Created user: {user['name']}")
    except Exception as e:
        print(f"Error seeding users: {e}")
        sys.exit(1)
    finally:
        conn.close()

    # Fetch admin ID for document uploads
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", ("eval_admin@securerag.com",))
            admin_id = str(cur.fetchone()["id"])
    finally:
        conn.close()

    # 2. Seed Documents
    print("\n2. Ingesting Evaluation Documents...")
    for doc in EVAL_DOCS:
        # Check if already exists
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM documents WHERE title = %s", (doc["title"],))
                exists = cur.fetchone()
        finally:
            conn.close()

        if exists:
            print(f"  Document '{doc['title']}' already exists. Skipping.")
            continue

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as temp:
            temp.write(doc["content"])
            temp_path = temp.name

        try:
            ingested = ingest_document(
                file_path=temp_path,
                title=doc["title"],
                department=doc["department"],
                sensitivity_level=doc["sensitivity_level"],
                uploaded_by_id=admin_id
            )
            print(f"  Ingested: {doc['title']} -> ID: {ingested['id']}")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    # 3. Apply Granular Metadata Override (Sensitivity=2 for salary bands in doc_hr_policy)
    print("\n3. Enforcing Mixed Sensitivity Levels (Salary Bands -> L2)...")
    # Search for the chunk containing 'Salary bands' in Qdrant
    points = client.scroll(
        collection_name=QDRANT_COLLECTION,
        limit=100,
        with_payload=True
    )[0]

    hr_policy_salary_chunk_id = None
    for pt in points:
        text = pt.payload.get("text", "")
        if "salary bands" in text.lower():
            hr_policy_salary_chunk_id = pt.id
            print(f"  Found salary bands chunk. Index: {pt.payload.get('chunk_index')} | ID: {pt.id}")
            # Update payload to sensitivity = 2 and department = all for the boundary test
            client.set_payload(
                collection_name=QDRANT_COLLECTION,
                payload={
                    "sensitivity_level": 2,
                    "department": "all"
                },
                points=[pt.id]
            )
            print("  [OK] Updated sensitivity_level to 2 (manager-only override) for salary bands chunk.")
            break

    if not hr_policy_salary_chunk_id:
        print("  [Warning] Could not find salary bands chunk to override.")

    # 4. Inject Missing-Metadata Chunk (fail-closed test)
    print("\n4. Injecting Chunk with Missing/Null Metadata...")
    # Generate dummy embedding
    vectors = embed_chunks(["This is a secret document chunk that contains restricted details but lacks sensitivity_level metadata."])
    dummy_vector = vectors[0]

    # Verify if dummy chunk already exists
    dummy_point_id = "00000000-0000-0000-0000-000000000000"
    client.upsert(
        collection_name=QDRANT_COLLECTION,
        points=[
            PointStruct(
                id=dummy_point_id,
                vector=dummy_vector,
                payload={
                    "text": "This is a secret document chunk that contains restricted details but lacks sensitivity_level metadata.",
                    "document_id": str(uuid.uuid4()),
                    # department and sensitivity_level are intentionally omitted!
                }
            )
        ]
    )
    print("  [OK] Ingested chunk with null department and sensitivity_level metadata.")

    print("\nEvaluation Seeding Completed successfully!")


if __name__ == "__main__":
    seed_eval()
