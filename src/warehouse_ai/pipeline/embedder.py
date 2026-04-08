"""Embedding generation: local sentence-transformers or OpenAI API."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from warehouse_ai.config import settings

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_local_model = None


def _get_local_model():
    """Lazy-load the local sentence-transformer model."""
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer

        _local_model = SentenceTransformer(settings.embedding_model)
        logger.info("Loaded local embedding model: %s", settings.embedding_model)
    return _local_model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts.

    Uses OpenAI API if configured, otherwise falls back to a local
    sentence-transformer model.
    """
    if not texts:
        return []

    if settings.llm_configured:
        return _embed_openai(texts)
    return _embed_local(texts)


def embed_query(text: str) -> list[float]:
    """Generate an embedding for a single query text."""
    return embed_texts([text])[0]


def _embed_local(texts: list[str]) -> list[list[float]]:
    """Embed using a local sentence-transformer model."""
    model = _get_local_model()
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return [e.tolist() for e in embeddings]


def _embed_openai(texts: list[str]) -> list[list[float]]:
    """Embed using the OpenAI API."""
    import openai

    client = openai.OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
    )

    # OpenAI batch limit is 2048 texts
    all_embeddings: list[list[float]] = []
    batch_size = 2048
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = client.embeddings.create(
            input=batch,
            model="text-embedding-3-small",
        )
        all_embeddings.extend([item.embedding for item in response.data])

    return all_embeddings


def get_embedding_dimension() -> int:
    """Return the dimension of the embedding model in use."""
    if settings.llm_configured:
        return 1536  # text-embedding-3-small
    return settings.embedding_dimension
