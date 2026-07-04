"""
Service layer for talking to the OpenAI API.

Views never call OpenAI directly; they go through ask_question() so the
integration is testable (mock this module) and swappable.

The assistant grounds its answers in a reference text file that has been
uploaded to an OpenAI vector store (see the upload_reference management
command). If OPENAI_VECTOR_STORE_ID is unset the assistant still works,
just without file search.
"""

from django.conf import settings
from openai import OpenAI, OpenAIError

INSTRUCTIONS = (
    "You are the Carnegie Mellon University Course Scheduling Assistant. "
    "You help students with questions about courses, prerequisites, and "
    "semester planning. When a reference document is available via file "
    "search, base your answers on it and say so when the document does "
    "not cover the question. Keep answers concise."
)


class AssistantError(Exception):
    """Raised when the assistant cannot produce an answer."""


def ask_question(question: str) -> str:
    """Send a question to OpenAI and return the assistant's answer text."""
    if not settings.OPENAI_API_KEY:
        raise AssistantError(
            "OPENAI_API_KEY is not set. Add it to the .env file in the "
            "project root and restart the server."
        )

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    kwargs: dict = {
        "model": settings.OPENAI_MODEL,
        "instructions": INSTRUCTIONS,
        "input": question,
    }
    if settings.OPENAI_VECTOR_STORE_ID:
        kwargs["tools"] = [
            {
                "type": "file_search",
                "vector_store_ids": [settings.OPENAI_VECTOR_STORE_ID],
            }
        ]

    try:
        response = client.responses.create(**kwargs)
    except OpenAIError as exc:
        raise AssistantError(f"OpenAI request failed: {exc}") from exc

    answer = response.output_text
    if not answer:
        raise AssistantError("OpenAI returned an empty response.")
    return answer
