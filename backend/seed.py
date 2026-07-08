"""
SecureRAG Data Seeding Script.

Creates seed users and ingests sample documents with different role/clearance boundaries.
"""

import os
import sys
import tempfile

# Add current directory to path so app modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.auth import hash_password
from app.database import get_connection, init_db
from app.vector_db import init_collection
from app.services.ingestion import ingest_document

# Seed Users Definition
SEED_USERS = [
    {
        "email": "alice@securerag.com",
        "password": "password123",
        "name": "Alice Smith",
        "role": "engineer",
        "department": "engineering",
        "clearance_level": 0,
    },
    {
        "email": "bob@securerag.com",
        "password": "password123",
        "name": "Bob Jones",
        "role": "manager",
        "department": "engineering",
        "clearance_level": 1,
    },
    {
        "email": "carol@securerag.com",
        "password": "password123",
        "name": "Carol Vance",
        "role": "hr",
        "department": "hr",
        "clearance_level": 2,
    },
    {
        "email": "admin@securerag.com",
        "password": "password123",
        "name": "Super Admin",
        "role": "admin",
        "department": "admin",
        "clearance_level": 3,
    },
]

# Seed Documents Content
DOCS_DATA = [
    {
        "title": "Engineering Handbook",
        "filename": "engineering_handbook.txt",
        "department": "all",
        "sensitivity_level": 0,
        "content": """
SecureRAG Engineering Code Quality and Standards Guidelines.
This document outlines the standard coding practices and architectural guidelines for all software engineers working at SecureRAG. 

Section 1: Version Control and Git Guidelines
Every code change must be tracked using Git. Engineers are required to work on feature branches named in the format 'feature/ticket-number-description'. Direct commits to the 'main' or 'master' branch are strictly prohibited. Before a pull request can be merged, it must undergo a peer review by at least one other engineer. Code reviews should verify that unit tests cover all modified code paths and that the code compiles without warnings. 

Section 2: Testing Best Practices
Unit testing is a mandatory component of our development lifecycle. We use pytest for Python development and Jest for JavaScript/React projects. A minimum of 80% code coverage is required for all new features. Automated integration tests are executed within our CI/CD pipeline on every push to remote repositories. When writing tests, engineers must mock external dependencies (such as third-party APIs and cloud vector databases) to ensure the test suite executes quickly and reliably without external network calls.

Section 3: System Design and Coding Styles
We follow the Clean Code principles. Variable names must be descriptive and follow snake_case in Python and camelCase in JavaScript. Functions should be small and single-purpose, containing no more than 50 lines of code. For API developments, we strictly utilize FastAPI due to its performance, asynchronous capability, and automatic OpenAPI documentation generation. In order to keep database queries fast, index all lookup columns and perform load testing on any queries expected to run in hot code paths.

Section 4: Deployment and CI/CD
Our deployment process is automated using GitHub Actions. Upon a successful merge to the 'main' branch, code is built, tested, and deployed to our staging environment. Production deployments occur weekly after manual verification from the QA team. Engineers must ensure that environment variables and secret tokens are never committed to git repositories. All environment configurations must be managed securely through the deployment dashboard.
"""
    },
    {
        "title": "HR Compensation Policy",
        "filename": "hr_policy.txt",
        "department": "hr",
        "sensitivity_level": 1,
        "content": """
SecureRAG Human Resources Compensation and Benefits Policy.
This policy governs the salary structures, promotions, and compensation reviews for all staff levels across the organization.

Section 1: Salary Band Structure and Career Levels
Compensation at SecureRAG is structured around defined Career Levels (L1 through L5). Each level represents a specific band of responsibilities, expectations, and base salary.
- Level L1 (Associate Engineer): Base salary ranges from $60,000 to $80,000 annually. This level is for entry-level developers and interns transitioning to full-time roles.
- Level L2 (Software Engineer): Base salary ranges from $85,000 to $110,000 annually. Candidates must demonstrate independent task completion and sound coding practices.
- Level L3 (Senior Engineer): Base salary ranges from $115,000 to $145,000 annually. L3 engineers are expected to design sub-systems and mentor junior developers.
- Level L4 (Staff Engineer): Base salary ranges from $150,000 to $185,000 annually. Staff engineers drive technical architecture across multiple teams and collaborate directly with leadership.
- Level L5 (Principal Engineer): Base salary ranges from $190,000 to $240,000 annually. L5 engineers are technical experts who shape company-wide engineering strategy and research initiatives.

Section 2: Annual Performance Reviews and Adjustments
Performance evaluations take place annually in November. The evaluation scores directly determine salary hikes and performance bonuses. The review process is split into self-assessments, peer feedback, and manager reviews. Employees scoring 'Exceeds Expectations' are eligible for a 7% to 12% salary adjustment. Those scoring 'Outstanding' may receive up to a 15% adjustment along with promotion consideration.

Section 3: Referral Bonuses and Benefits
We encourage employees to refer high-quality candidates to our open positions. If a referred candidate is hired and completes their 3-month probation period, the referring employee receives a $3,000 referral bonus. Additional health benefits, retirement matching, and learning stipends are detailed in the employee benefits portal. Any disputes regarding compensation must be raised directly to the HR department via the official ticketing system.
"""
    },
    {
        "title": "Legal Client Agreement - Client X",
        "filename": "legal_contract.txt",
        "department": "legal",
        "sensitivity_level": 2,
        "content": """
CONFIDENTIAL MUTUAL NON-DISCLOSURE AND SERVICE AGREEMENT
This Agreement is entered into by and between SecureRAG Inc. ('Company') and Client X Corporation ('Client').

Section 1: Scope of Services and Deliverables
Company agrees to provide advanced secure document processing services, including custom vector storage setup, private LLM gateway hosting, and query auditing infrastructure. The service contract is valued at a total of $450,000, payable in monthly installments upon milestone completion. The initial term of this agreement is twelve (12) months, starting on June 1, 2026. The contract will automatically renew for subsequent twelve-month periods unless terminated by either party with 60 days written notice prior to renewal.

Section 2: Intellectual Property and Ownership
All software, designs, API patterns, and RAG architectures developed by the Company prior to or during this engagement remain the exclusive intellectual property of the Company. The Client is granted a non-exclusive, non-transferable license to use the system for internal operations. The Client agrees not to reverse engineer, decompile, or copy the RAG query filtering algorithms. Client data uploaded to the system remains the sole property of the Client.

Section 3: Confidentiality and Data Protection
Both parties agree to protect the Confidential Information of the other party with the same degree of care they use to protect their own proprietary information, but no less than a reasonable standard of care. Confidential Information includes all codebases, pricing models, security policies, and user data. In the event of a data breach, the affected party must notify the other within 24 hours of discovery and outline remediation steps.

Section 4: Indemnification and Liability
Neither party shall be liable for indirect, incidental, or consequential damages, including loss of profits or revenue, arising from this agreement. The total liability of the Company under this contract is capped at the total amount paid by the Client to the Company during the six months preceding the event giving rise to the claim. Any dispute arising from this contract will be resolved through binding arbitration under the laws of the State of California.
"""
    },
    {
        "title": "Q1 Strategic Financial Report",
        "filename": "company_finances.txt",
        "department": "admin",
        "sensitivity_level": 3,
        "content": """
RESTRICTED: SECURERAG Q1 EXECUTIVE FINANCIAL REPORT AND STRATEGIC PLAN
This report is strictly confidential and restricted to executive leadership and senior administrators.

Section 1: Q1 Revenue and Expenditure Analysis
During the first quarter of the fiscal year, SecureRAG recorded total revenues of $1,850,000, representing a 24% year-over-year growth. The main drivers of revenue were enterprise SaaS subscriptions and specialized security compliance auditing services. Operating expenses totaled $1,200,000, of which $750,000 was allocated to engineering salaries and $250,000 to cloud hosting costs across AWS and Neon. The resulting net profit for Q1 stands at $650,000.

Section 2: Funding Round and Runway Plan
We are currently in active discussions with venture capital partners for a Series A funding round. Our goal is to raise $8,000,000 at a post-money valuation of $40,000,000. This capital will be utilized to double our engineering staff, establish a presence in the APAC market, and invest in hardware for local model inference. Our current cash reserves provide a runway of approximately 18 months under current operating expenditure.

Section 3: Mergers, Acquisitions, and Market Strategy
Our expansion plan includes the potential acquisition of a smaller vector index compression startup. This acquisition would give us proprietary quantization technology, reducing vector memory footprints by up to 60%. A budget of $1,500,000 has been set aside for this M&A activity, with due diligence scheduled to begin next quarter. Any leakage of this information violates internal security policies and will result in immediate termination.

Section 4: Risk Mitigation and Projections
Key risks include fluctuating GPU cloud pricing and increased competition in the secure enterprise search sector. To mitigate these risks, we are negotiating long-term pricing contracts with server providers and securing patent protection for our query-time pre-filtering mechanisms. For Q2, we project a revenue increase of 15%, targeting a net profit margin of 35% through operational efficiencies.
"""
    }
]


def seed_database():
    """Initialise and seed the Postgres database and Qdrant vector store."""
    print("--- SecureRAG Database Seeding Process ---")
    
    # 1. Initialize databases
    print("Initialising Postgres database schema...")
    init_db()
    
    print("Initialising Qdrant collection...")
    init_collection()

    conn = get_connection()
    admin_id = None
    
    # 2. Seed Users
    print("\nSeeding user accounts...")
    try:
        with conn.cursor() as cur:
            for user in SEED_USERS:
                # Check if user already exists
                cur.execute("SELECT id FROM users WHERE email = %s", (user["email"],))
                existing = cur.fetchone()
                
                if existing:
                    print(f"User {user['email']} already exists. Skipping.")
                    if user["role"] == "admin":
                        admin_id = str(existing["id"])
                    continue
                
                hashed = hash_password(user["password"])
                cur.execute(
                    """
                    INSERT INTO users (email, password_hash, name, role, department, clearance_level)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (user["email"], hashed, user["name"], user["role"], user["department"], user["clearance_level"])
                )
                new_id = str(cur.fetchone()["id"])
                print(f"Created user: {user['name']} ({user['email']}) -> Role: {user['role']}")
                if user["role"] == "admin":
                    admin_id = new_id
    except Exception as e:
        print(f"Error seeding users: {e}")
        conn.close()
        sys.exit(1)
    finally:
        conn.close()

    # If admin already existed but we didn't capture the ID
    if not admin_id:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
                row = cur.fetchone()
                if row:
                    admin_id = str(row["id"])
        finally:
            conn.close()

    # 3. Seed Documents
    print("\nIngesting seed documents into Postgres and Qdrant...")
    for doc in DOCS_DATA:
        # Check if document already ingested
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM documents WHERE title = %s", (doc["title"],))
                existing_doc = cur.fetchone()
        finally:
            conn.close()

        if existing_doc:
            print(f"Document '{doc['title']}' already exists. Skipping ingestion.")
            continue

        # Write to a temporary file for the ingestion pipeline to process
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as temp:
            temp.write(doc["content"])
            temp_path = temp.name

        try:
            print(f"Ingesting: '{doc['title']}' (Dept: {doc['department']}, Sensitivity: {doc['sensitivity_level']})")
            ingested_doc = ingest_document(
                file_path=temp_path,
                title=doc["title"],
                department=doc["department"],
                sensitivity_level=doc["sensitivity_level"],
                uploaded_by_id=admin_id
            )
            print(f"Successfully ingested document ID: {ingested_doc['id']}")
        except Exception as e:
            print(f"Error ingesting '{doc['title']}': {e}")
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    print("\n--- Seeding Process Completed Successfully! ---")


if __name__ == "__main__":
    seed_database()
