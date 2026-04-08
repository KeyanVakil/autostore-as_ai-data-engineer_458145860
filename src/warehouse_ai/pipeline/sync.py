"""Sync embeddings from Delta Lake chunks table to ChromaDB."""

from __future__ import annotations

import json
import logging

from warehouse_ai.storage.delta import DeltaStore
from warehouse_ai.storage.vector import VectorStore

logger = logging.getLogger(__name__)


def sync_to_chromadb(delta: DeltaStore, vector: VectorStore) -> int:
    """Sync all chunks with embeddings from Delta Lake to ChromaDB.

    Returns the number of chunks synced.
    """
    chunks = delta.get_all_chunks_with_embeddings()
    if not chunks:
        logger.info("No chunks with embeddings to sync")
        return 0

    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for chunk in chunks:
        ids.append(chunk["chunk_id"])
        embeddings.append(chunk["embedding"])
        documents.append(chunk["content"])

        meta = {}
        if chunk.get("metadata"):
            try:
                meta = json.loads(chunk["metadata"]) if isinstance(chunk["metadata"], str) else chunk["metadata"]
            except (json.JSONDecodeError, TypeError):
                meta = {}
        meta["document_id"] = chunk["document_id"]
        meta["chunk_index"] = chunk["chunk_index"]
        metadatas.append(meta)

    vector.add_chunks(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    logger.info("Synced %d chunks to ChromaDB", len(ids))
    return len(ids)
