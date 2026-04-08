"""ChromaDB vector store wrapper."""

from __future__ import annotations

import logging

import chromadb
from chromadb.config import Settings as ChromaSettings

from warehouse_ai.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Thin wrapper around ChromaDB for document chunk embeddings."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        collection_name: str | None = None,
    ):
        self._host = host or settings.chroma_host
        self._port = port or settings.chroma_port
        self._collection_name = collection_name or settings.chroma_collection
        self._client: chromadb.ClientAPI | None = None
        self._collection: chromadb.Collection | None = None

    def _get_client(self) -> chromadb.ClientAPI:
        if self._client is None:
            self._client = chromadb.HttpClient(
                host=self._host,
                port=self._port,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client

    def _get_collection(self) -> chromadb.Collection:
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def add_chunks(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict] | None = None,
    ) -> None:
        """Add document chunks with their embeddings to the vector store."""
        collection = self._get_collection()
        # ChromaDB has a batch limit — split into batches of 5000
        batch_size = 5000
        for i in range(0, len(ids), batch_size):
            end = i + batch_size
            collection.upsert(
                ids=ids[i:end],
                embeddings=embeddings[i:end],
                documents=documents[i:end],
                metadatas=metadatas[i:end] if metadatas else None,
            )
        logger.info("Added %d chunks to vector store", len(ids))

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        min_score: float = 0.3,
        where: dict | None = None,
    ) -> list[dict]:
        """Search for similar chunks, returning results above the min_score threshold."""
        collection = self._get_collection()
        kwargs: dict = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where
        results = collection.query(**kwargs)

        hits = []
        for i, chunk_id in enumerate(results["ids"][0]):
            # ChromaDB returns cosine distance; convert to similarity
            distance = results["distances"][0][i]
            similarity = 1.0 - distance
            if similarity < min_score:
                continue
            hits.append(
                {
                    "chunk_id": chunk_id,
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "relevance_score": round(similarity, 4),
                }
            )
        return hits

    def count(self) -> int:
        return self._get_collection().count()

    def heartbeat(self) -> bool:
        try:
            self._get_client().heartbeat()
            return True
        except Exception:
            return False

    def reset_collection(self) -> None:
        client = self._get_client()
        try:
            client.delete_collection(self._collection_name)
        except Exception:
            pass
        self._collection = None
