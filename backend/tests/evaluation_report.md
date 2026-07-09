# SecureRAG RBAC-RAG Quantitative Evaluation Report

This report presents a quantitative evaluation of the **SecureRAG** role-based access control and retrieval-augmented generation pipeline. It benchmarks classification accuracy, latency overhead cost, and context grounding.

---

## 1. Access Control Metrics (Classification Analysis)

Analyzes the full user-chunk matching matrix across the database users and vector collection points.

- **Total Chunks Evaluated**: 28
- **Total Users Evaluated**: 4
- **Total Decision Pairs**: 112

| Metric | Measured Value | Target Goal | Status |
| :--- | :--- | :--- | :--- |
| **False Positives (FP) / Leakages** | **0** | **0** | **PASS** |
| Leakage Rate | 0.00% | 0.0% | **PASS** |
| Access Precision | 100.00% | 100.0% | **PASS** |
| Access Recall | 100.00% | 100.0% (No False Negatives) | 100% Legitimate Access |
| Overall Classification Accuracy | 100.00% | &gt;95.0% | **PASS** |

### Confusion Matrix Detail
- **True Positives (TP)**: 56 (Authorized chunks correctly retrieved)
- **False Positives (FP)**: 0 (Unauthorized chunks incorrectly retrieved)
- **True Negatives (TN)**: 56 (Unauthorized chunks correctly blocked)
- **False Negatives (FN)**: 0 (Authorized chunks incorrectly blocked)

*A visual vector graphic of the confusion matrix is available in [evaluation_confusion_matrix.svg](evaluation_confusion_matrix.svg).*

---

## 2. Latency Overhead Benchmark

Measures vector database query performance comparison with and without the secure RBAC pre-filter (runs = 60).

| Query Type | Mean Latency | Standard Deviation | Median (p50) | p95 Latency |
| :--- | :--- | :--- | :--- | :--- |
| **RBAC Filtered Search** | 454.82 ms | ± 3.45 ms | 454.14 ms | 461.23 ms |
| **Baseline Search (No Filter)** | 231.69 ms | ± 63.37 ms | 222.75 ms | 231.97 ms |

- **RBAC Latency Overhead**: **96.31%**

*Note: The overhead measures only the database vector retrieval filter operation, isolating it from downstream LLM generative latency.*

---

## 3. RAG Quality and Grounding

Evaluates the relevance of context chunks and the grounding of the generated answers against a set of 12 labeled reference questions.

| Quality Metric | Measured Value | Description |
| :--- | :--- | :--- |
| **Retrieval Precision@5** | 100.00% | Percentage of queries retrieving the exact correct source context. |
| **Mean Groundedness (LLM-as-judge)** | 1.00 / 1.00 | Average rating of generated answer factual support. |
| **Hallucination Rate** | 0.00% | Percentage of generated answers containing claims unsupported by context. |
