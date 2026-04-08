"""FastAPI dependency injection for shared services."""

from __future__ import annotations

import logging
from typing import Any

from warehouse_ai.agent.graph import create_rag_agent
from warehouse_ai.config import settings
from warehouse_ai.pipeline.spark import get_spark_session
from warehouse_ai.storage.delta import DeltaStore
from warehouse_ai.storage.vector import VectorStore

logger = logging.getLogger(__name__)

_spark = None
_delta: DeltaStore | None = None
_vector: VectorStore | None = None
_agent: Any = None


def get_spark():
    global _spark
    if _spark is None:
        _spark = get_spark_session(delta_path=settings.delta_lake_path)
    return _spark


def get_delta() -> DeltaStore:
    global _delta
    if _delta is None:
        _delta = DeltaStore(get_spark(), settings.delta_lake_path)
        _delta.init_tables()
    return _delta


def get_vector() -> VectorStore:
    global _vector
    if _vector is None:
        _vector = VectorStore(
            host=settings.chroma_host,
            port=settings.chroma_port,
            collection_name=settings.chroma_collection,
        )
    return _vector


def get_agent():
    global _agent
    if _agent is None:
        _agent = create_rag_agent(get_delta(), get_vector())
    return _agent


def reset_dependencies() -> None:
    """Reset all cached dependencies (used in testing)."""
    global _spark, _delta, _vector, _agent
    _spark = None
    _delta = None
    _vector = None
    _agent = None
