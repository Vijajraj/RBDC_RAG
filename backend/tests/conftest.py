"""
Shared Pytest Config and Hook Implementations.
Saves evaluation results to backend/tests/evaluation_results.md using pytest namespace.
"""

import os
import pytest


def pytest_sessionfinish(session, exitstatus):
    """Executes at the end of the test session to print and save matrices/reports."""
    output_lines = []
    
    # Retrieve results from pytest global namespace
    access_matrix_results = getattr(pytest, "access_matrix_results", [])
    rag_quality_results = getattr(pytest, "rag_quality_results", [])
    
    # 1. Print and Format Access Matrix
    if access_matrix_results:
        matrix_title = "SECURERAG EVALUATION: ACCESS CORRECTNESS MATRIX RESULT SUMMARY"
        output_lines.append(f"# {matrix_title}\n")
        
        # Markdown table header
        output_lines.append("| USER | DOCUMENT | EXPECTED | ACTUAL | CHUNKS | STATUS |")
        output_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        
        for res in access_matrix_results:
            output_lines.append(
                f"| {res['user']} | {res['doc']} | {res['expected']} | {res['actual']} | {res['chunks']} | {res['passed']} |"
            )
        output_lines.append("\n")

    # 2. Print and Format RAG Quality Report
    if rag_quality_results:
        quality_title = "SECURERAG EVALUATION: RAG QUALITY & GROUNDING REPORT"
        output_lines.append(f"# {quality_title}\n")
        
        # Markdown table header
        output_lines.append("| QUESTION | DOC | RELEVANCE | GROUNDED | STATUS |")
        output_lines.append("| :--- | :--- | :--- | :--- | :--- |")
        
        for q in rag_quality_results:
            output_lines.append(
                f"| {q['question']} | {q['doc']} | {q['relevance']} | {q['grounding']} | {q['passed']} |"
            )
        output_lines.append("\n")

    # Save to file
    if output_lines:
        report_path = os.path.join(os.path.dirname(__file__), "evaluation_results.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(output_lines))
        print(f"\n[Evaluation Report] Saved matrix and reports to: {report_path}")
