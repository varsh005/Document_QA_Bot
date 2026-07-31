"""
Embeddings + vector store service.

Each Document gets its own FAISS index file on disk, keyed by document id.
Keeping one index per document (rather than one giant shared index) keeps
retrieval scoped correctly - a question about Document A should never
retrieve chunks from Document B.

Uses Google's Gemini API for embeddings (free tier, no credit card needed).
"""
import os
import faiss
import numpy as np
import google.generativeai as genai
from django.conf import settings

_configured = False


def _ensure_configured():
    global _configured
    if not _configured:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to your .env file - see .env.example. "
                "Get a free key at https://aistudio.google.com/apikey"
            )
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _configured = True


def embed_texts(texts: list[str]) -> np.ndarray:
    """Call Gemini's embeddings endpoint for a batch of texts. Returns float32 array."""
    _ensure_configured()
    vectors = []
    for text in texts:
        result = genai.embed_content(model=settings.EMBEDDING_MODEL, content=text)
        vectors.append(result['embedding'])
    return np.array(vectors, dtype='float32')


def _index_path(document_id) -> str:
    settings.VECTOR_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    return str(settings.VECTOR_INDEX_DIR / f"{document_id}.index")


def build_index(document_id, chunk_texts: list[str]) -> None:
    """Embed all chunks for a document and persist a fresh FAISS index for it."""
    vectors = embed_texts(chunk_texts)
    # Normalize so inner product == cosine similarity.
    faiss.normalize_L2(vectors)

    dimension = vectors.shape[1]
    index = faiss.IndexFlatIP(dimension)  # exact search, inner product
    index.add(vectors)

    faiss.write_index(index, _index_path(document_id))


def load_index(document_id):
    path = _index_path(document_id)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"No vector index found for document {document_id}. It may still be processing."
        )
    return faiss.read_index(path)


def search(document_id, query: str, top_k: int = None) -> list[tuple[int, float]]:
    """
    Embed the query and return the top_k most similar chunk positions
    for this document, as (vector_index_position, similarity_score) pairs.
    """
    top_k = top_k or settings.TOP_K_CHUNKS
    index = load_index(document_id)

    query_vector = embed_texts([query])
    faiss.normalize_L2(query_vector)

    scores, positions = index.search(query_vector, top_k)
    results = []
    for pos, score in zip(positions[0], scores[0]):
        if pos == -1:
            continue
        results.append((int(pos), float(score)))
    return results


def delete_index(document_id) -> None:
    path = _index_path(document_id)
    if os.path.exists(path):
        os.remove(path)
