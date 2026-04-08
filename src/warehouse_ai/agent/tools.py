"""Agent tools for vector search and document lookup."""

from __future__ import annotations

import json
import logging
from typing import Any

from warehouse_ai.config import settings
from warehouse_ai.pipeline.embedder import embed_query
from warehouse_ai.storage.delta import DeltaStore
from warehouse_ai.storage.vector import VectorStore

logger = logging.getLogger(__name__)


def vector_search(
    query: str,
    vector: VectorStore,
    top_k: int | None = None,
    min_score: float | None = None,
    filters: dict | None = None,
) -> list[dict[str, Any]]:
    """Search for relevant document chunks using vector similarity."""
    embedding = embed_query(query)
    results = vector.search(
        query_embedding=embedding,
        top_k=top_k or settings.retrieval_top_k,
        min_score=min_score or settings.similarity_threshold,
        where=filters,
    )
    return results


def get_document_info(document_id: str, delta: DeltaStore) -> dict[str, Any] | None:
    """Look up document metadata by ID."""
    docs = delta.list_documents()
    for doc in docs:
        if doc["document_id"] == document_id:
            return doc
    return None


def get_chunk_context(
    chunk_ids: list[str], delta: DeltaStore
) -> list[dict[str, Any]]:
    """Retrieve full chunk data from Delta Lake by IDs."""
    return delta.get_chunks_by_ids(chunk_ids)
