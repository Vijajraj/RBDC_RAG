# SECURERAG EVALUATION: ACCESS CORRECTNESS MATRIX RESULT SUMMARY

| USER | DOCUMENT | EXPECTED | ACTUAL | CHUNKS | STATUS |
| :--- | :--- | :--- | :--- | :--- | :--- |
| engineer | doc_engineering | Allowed | Allowed | 1 | PASS |
| engineer | doc_hr_policy | Blocked | Blocked | 0 | PASS |
| engineer | doc_legal_contract | Blocked | Blocked | 0 | PASS |
| engineer | doc_finance_q1 | Blocked | Blocked | 0 | PASS |
| manager | doc_engineering | Allowed | Allowed | 1 | PASS |
| manager | doc_hr_policy | Allowed | Allowed | 1 | PASS |
| manager | doc_legal_contract | Blocked | Blocked | 0 | PASS |
| manager | doc_finance_q1 | Blocked | Blocked | 0 | PASS |
| hr_admin | doc_engineering | Blocked | Blocked | 0 | PASS |
| hr_admin | doc_hr_policy | Allowed | Allowed | 2 | PASS |
| hr_admin | doc_legal_contract | Blocked | Blocked | 0 | PASS |
| hr_admin | doc_finance_q1 | Blocked | Blocked | 0 | PASS |
| admin | doc_engineering | Allowed | Allowed | 1 | PASS |
| admin | doc_hr_policy | Allowed | Allowed | 2 | PASS |
| admin | doc_legal_contract | Allowed | Allowed | 1 | PASS |
| admin | doc_finance_q1 | Allowed | Allowed | 1 | PASS |


# SECURERAG EVALUATION: RAG QUALITY & GROUNDING REPORT

| QUESTION | DOC | RELEVANCE | GROUNDED | STATUS |
| :--- | :--- | :--- | :--- | :--- |
| What guidelines are listed in the Engine... | doc_engineering | YES | YES | PASS |
| When do CI/CD deployments run automatica... | doc_engineering | YES | YES | PASS |
| What processes should all engineers foll... | doc_engineering | YES | YES | PASS |
| What are the core working hours at Secur... | doc_hr_policy | YES | YES | PASS |
| What percentage pension matching is offe... | doc_hr_policy | YES | YES | PASS |
| What is the base salary range for L3 Sen... | doc_hr_policy | YES | YES | PASS |
| What is the total annual value of the se... | doc_legal_contract | YES | YES | PASS |
| Under what state's jurisdiction will con... | doc_legal_contract | YES | YES | PASS |
| What proprietary clauses are detailed in... | doc_legal_contract | YES | YES | PASS |
| What was the total revenue recorded by S... | doc_finance_q1 | YES | YES | PASS |
| What post-money valuation is targeted fo... | doc_finance_q1 | YES | YES | PASS |
| How many months of runway do current cas... | doc_finance_q1 | YES | YES | PASS |

