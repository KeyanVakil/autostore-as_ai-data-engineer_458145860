"""Vector search endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from warehouse_ai.api.dependencies import get_delta, get_vector
from warehouse_ai.api.models import SearchRequest, SearchResponse, SearchResult
from warehouse_ai.agent.tools import get_document_info, vector_search
from warehouse_ai.storage.delta import DeltaStore
from warehouse_ai.storage.vector import VectorStore

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    delta: DeltaStore = Depends(get_delta),
    vector: VectorStore = Depends(get_vector),
):
    """Semantic search across ingested documents."""
    results = vector_search(
        query=request.query,
        vector=vector,
        top_k=request.top_k,
        min_score=request.min_score,
        filters=request.filters,
    )

    search_results = []
    for r in results:
        doc_id = r.get("metadata", {}).get("document_id", "")
        doc_info = get_document_info(doc_id, delta) if doc_id else None
        doc_title = doc_info["title"] if doc_info else "Unknown"

        search_results.append(
            SearchResult(
                chunk_id=r["chunk_id"],
                document_title=doc_title,
                content=r["content"],
                relevance_score=r["relevance_score"],
            )
        )

    return SearchResponse(results=search_results)
