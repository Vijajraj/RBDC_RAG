"""
SecureRAG LLM Service.

Wraps the Groq SDK to call llama-3.3-70b-versatile with
retrieved context chunks and role-aware prompting.
"""

from __future__ import annotations

from typing import Any, Dict, List

from groq import Groq

from app.config import GROQ_API_KEY

# ---------------------------------------------------------------------------
# Groq client singleton
# ---------------------------------------------------------------------------
_groq_client: Groq | None = None


def _get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=GROQ_API_KEY)
    return _groq_client


# ---------------------------------------------------------------------------
# Answer generation
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are SecureRAG, an AI assistant integrated into a role-based access control (RBAC) document retrieval system.

You answer questions **only** based on the context chunks provided below.
If the context does not contain enough information to answer, say so clearly.

Important guidelines:
- Be concise, factual, and helpful.
- Do NOT fabricate information that is not in the provided context.
- Reference relevant details from the context to support your answer.
- The user's role and department information is provided for context awareness — tailor the tone accordingly.
"""


def generate_answer(
    query: str,
    context_chunks: List[str],
    role_info: Dict[str, Any],
) -> str:
    """Send the query + context to Groq and return the LLM's answer.

    Parameters
    ----------
    query : str
        The user's natural-language question.
    context_chunks : list[str]
        Retrieved text chunks the user is allowed to see.
    role_info : dict
        Must contain at least ``role``, ``department``, and ``clearance_level``.
    """
    client = _get_groq_client()

    # Build the context block
    if context_chunks:
        context_text = "\n\n---\n\n".join(
            f"[Chunk {i + 1}]\n{chunk}" for i, chunk in enumerate(context_chunks)
        )
    else:
        context_text = "(No context chunks were retrieved for this query.)"

    user_message = (
        f"User role: {role_info.get('role', 'unknown')} | "
        f"Department: {role_info.get('department', 'unknown')} | "
        f"Clearance Level: {role_info.get('clearance_level', 0)}\n\n"
        f"--- Retrieved Context ---\n{context_text}\n"
        f"--- End of Context ---\n\n"
        f"Question: {query}"
    )

    chat_completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
        max_tokens=1024,
    )

    return chat_completion.choices[0].message.content
