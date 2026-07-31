"""
RAG (Retrieval-Augmented Generation) service.

Ties retrieval (embeddings.search) together with generation (Gemini chat
completion), and is deliberately strict about only answering from the
supplied context so the bot doesn't quietly fall back on general knowledge.
"""
import google.generativeai as genai
from django.conf import settings
from documents.models import Chunk
from documents.services.embeddings import search, _ensure_configured

SYSTEM_PROMPT = (
    "You are a study assistant that answers questions using ONLY the "
    "provided document excerpts. Rules:\n"
    "1. If the excerpts don't contain the answer, say clearly that the "
    "document doesn't cover it - never invent information.\n"
    "2. Keep answers concise and direct, in the style of a helpful tutor.\n"
    "3. When useful, refer to which part of the material you're drawing from "
    "(e.g. 'According to the section on...').\n"
)


def answer_question(document, question: str, chat_history: list[dict] = None) -> dict:
    """
    Run the full RAG flow for one question against one document.

    Returns a dict with the answer text and the Chunk objects used as sources,
    so the caller can store/display citations.
    """
    results = search(document.id, question)
    positions = [pos for pos, _score in results]

    chunks = list(
        Chunk.objects.filter(document=document, vector_index_position__in=positions)
    )
    # Preserve retrieval order (most relevant first), not DB order.
    chunks.sort(key=lambda c: positions.index(c.vector_index_position))

    if not chunks:
        return {
            'answer': "I couldn't find anything relevant to that in the document.",
            'chunks': [],
        }

    context = '\n\n---\n\n'.join(
        f"[Excerpt {i + 1}]\n{c.text}" for i, c in enumerate(chunks)
    )

    history_text = ''
    for turn in (chat_history or [])[-6:]:  # keep last few turns for follow-up questions
        speaker = 'User' if turn['role'] == 'user' else 'Assistant'
        history_text += f"{speaker}: {turn['content']}\n"

    prompt = (
        f"Document excerpts:\n\n{context}\n\n"
        + (f"Recent conversation:\n{history_text}\n\n" if history_text else '')
        + f"Question: {question}"
    )

    _ensure_configured()
    model = genai.GenerativeModel(settings.CHAT_MODEL, system_instruction=SYSTEM_PROMPT)
    response = model.generate_content(prompt)

    return {
        'answer': response.text,
        'chunks': chunks,
    }
