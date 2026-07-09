"""
SecureRAG LLM Service.

Wraps the Groq SDK to call llama-3.3-70b-versatile with
retrieved context chunks and role-aware prompting, including failover.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

from groq import Groq
import groq

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
    """Send the query + context to Groq and return the LLM's answer with automatic failover."""
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

    models_to_try = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    
    for i, model in enumerate(models_to_try):
        try:
            chat_completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.3,
                max_tokens=1024,
            )
            return chat_completion.choices[0].message.content
        except groq.RateLimitError as e:
            print(f"[LLM Service] Rate limit hit for model {model}. Error: {e}")
            if i < len(models_to_try) - 1:
                print(f"[LLM Service] Falling back to alternative model: {models_to_try[i+1]}...")
                continue
            else:
                # If we've run out of models to try, wait 3 seconds and retry the last model once
                time.sleep(3)
                try:
                    chat_completion = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_message},
                        ],
                        temperature=0.3,
                        max_tokens=1024,
                    )
                    return chat_completion.choices[0].message.content
                except Exception as final_e:
                    return f"System rate limit reached. Unable to generate response. Error: {final_e}"
        except Exception as e:
            return f"Error communicating with LLM service: {e}"
