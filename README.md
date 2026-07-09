# SecureRAG — Role-Based RAG Access Control System

SecureRAG is an enterprise-grade Retrieval-Augmented Generation (RAG) system built to enforce strict security boundaries. By utilizing role-based access control (RBAC), SecureRAG ensures that users can only retrieve and generate answers from documents they are explicitly authorized to access. 

The security-critical core of the system is **pure pre-filtration at the vector database search layer**. Chunks are filtered inside Qdrant itself before vectors are ever returned, guaranteeing that unauthorized data never enters the LLM context.

---

## 🚀 Key Features

- **Qdrant Pre-Filtration**: Permissions are enforced directly inside Qdrant's search call using `Filter` and `FieldCondition` models. This prevents data leakage and preserves search precision.
- **Fail-Closed on Missing Fields**: Any vector chunk missing `department` or `sensitivity_level` metadata is automatically blocked using presence-check `IsEmptyCondition` filters.
- **Transaction-Safe Auditing**: Retrieval audits and access denial reasons are recorded to a Postgres `audit_logs` table in the same transaction block as the RAG query to prevent data drift.
- **Claude-like Chat UI**: Features a sleek dark-themed workspace with a centered message log, wide action input bar, administrative upload panel, and collapsible **Access Trace** sidebar showing real-time allowed vs. denied chunk counts.
- **Automatic LLM Failover**: Smart model failover catches rate-limiting exceptions (`429`) on Groq and gracefully switches between models (e.g. `llama-3.3-70b-versatile` to `llama-3.1-8b-instant`).

---

## 📊 Quantitative Evaluation

We evaluated the SecureRAG system's security boundaries and query latency overhead using a standalone evaluation harness (**`evaluate.py`**) running against the actual cloud database instances.

### 1. Access Control Classification (100% Pass)
We analyzed the full matching matrix crossing **4 users** against all **28 chunks** currently stored in the Qdrant database (total of **112 unique pairs**).

| Metric | Measured Value | Target Goal | Status |
| :--- | :--- | :--- | :--- |
| **False Positives (FP) / Leakages** | **0** | **0** | **PASS** |
| **Leakage Rate** | **0.00%** | **0.0%** | **PASS** |
| **Access Precision** | **100.00%** | **100.0%** | **PASS** |
| **Access Recall** | **100.00%** | **100.0% (No false negatives)** | **PASS** |
| **Overall Classification Accuracy** | **100.00%** | **>95.0%** | **PASS** |

#### Confusion Matrix Details
- **True Positives (TP)**: 56 (Authorized chunks correctly retrieved)
- **False Positives (FP)**: 0 (Unauthorized chunks blocked and never leaked)
- **True Negatives (TN)**: 56 (Unauthorized chunks correctly blocked)
- **False Negatives (FN)**: 0 (Authorized chunks correctly allowed without over-restriction)

*A vector graphic of the confusion matrix is available in [tests/evaluation_confusion_matrix.svg](backend/tests/evaluation_confusion_matrix.svg).*

### 2. Latency Overhead Benchmark
We measured Qdrant vector search query performance with and without the secure RBAC pre-filter (20 runs per query across 3 sample queries, total = 60 runs).

| Query Type | Mean Latency | Standard Deviation | Median (p50) | p95 Latency |
| :--- | :--- | :--- | :--- | :--- |
| **RBAC Filtered Search** | 454.82 ms | ± 3.45 ms | 454.14 ms | 461.23 ms |
| **Baseline Search (No Filter)** | 231.69 ms | ± 63.37 ms | 222.75 ms | 231.97 ms |

- **RBAC Latency Overhead**: **96.31%** (adds ~223ms of processing overhead on CPU vector encoding and payload indexing lookup, which is completely unnoticeable when factored with downstream LLM generation).

### 3. RAG Quality & Groundedness
We evaluated chunk relevance and generated answer grounding against 12 reference question/answer pairs using an **LLM-as-a-judge** prompt (Llama-3.1-8b-instant):

| Quality Metric | Measured Value | Description |
| :--- | :--- | :--- |
| **Retrieval Precision@5** | 100.00% | Percentage of queries retrieving the exact correct source context. |
| **Mean Groundedness** | 1.00 / 1.00 | Average rating of generated answer factual support. |
| **Hallucination Rate** | 0.00% | Percentage of generated answers containing claims unsupported by context. |

---

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python), Uvicorn (ASGI Server), PostgreSQL (neon.tech), Qdrant (Cloud Vector DB), Groq (LLM Inference)
- **Frontend**: React, Vite, Tailwind CSS v4, Lucide Icons
- **Embedding**: FastEmbed (BAAI/bge-small-en-v1.5)

---

## 📂 Project Structure

```
RBDC_RAG/
├── backend/
│   ├── app/
│   │   ├── routes/          # Auth, Documents, Chat, Audit API routes
│   │   ├── services/        # Ingestion pipeline, LLM generation
│   │   ├── config.py        # Config & env validation
│   │   ├── database.py      # Postgres schema & migrations
│   │   ├── rbac.py          # Secure RBAC filter builder
│   │   └── main.py          # FastAPI startup & hooks
│   ├── tests/               # Pytest correctness & evaluate metrics
│   ├── requirements.txt
│   ├── seed.py              # Main corporate document seeder
│   └── evaluate.py          # Quantitative evaluation harness
└── frontend/                # React app with TailwindCSS v4
```

---

## ⚙️ Installation & Run Guide

### 1. Backend Setup
1. Navigate to the backend folder:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the Uvicorn local server:
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```

### 2. Frontend Setup
1. Navigate to the frontend folder:
   ```bash
   cd ../frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```

### 3. Running the Evaluation Harness
To execute the quantitative evaluation benchmark and update report files:
```bash
cd backend
.venv\Scripts\python.exe evaluate.py
```
This generates:
- `backend/tests/evaluation_results.json` (raw metrics)
- `backend/tests/evaluation_report.md` (markdown report)
- `backend/tests/evaluation_access_matrix.csv` (auditable rows)
- `backend/tests/evaluation_confusion_matrix.svg` (confusion matrix plot)