"""Delta Lake table operations for documents, chunks, chat history, and pipeline runs."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    ArrayType,
    FloatType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from warehouse_ai.config import settings

logger = logging.getLogger(__name__)

DOCUMENTS_SCHEMA = StructType(
    [
        StructField("document_id", StringType(), False),
        StructField("filename", StringType(), False),
        StructField("content_hash", StringType(), False),
        StructField("file_type", StringType(), False),
        StructField("file_size_bytes", LongType(), False),
        StructField("title", StringType(), True),
        StructField("ingested_at", TimestampType(), False),
        StructField("chunk_count", IntegerType(), False),
        StructField("status", StringType(), False),
    ]
)

CHUNKS_SCHEMA = StructType(
    [
        StructField("chunk_id", StringType(), False),
        StructField("document_id", StringType(), False),
        StructField("chunk_index", IntegerType(), False),
        StructField("content", StringType(), False),
        StructField("token_count", IntegerType(), False),
        StructField("embedding", ArrayType(FloatType()), True),
        StructField("metadata", StringType(), True),
        StructField("created_at", TimestampType(), False),
    ]
)

CHAT_HISTORY_SCHEMA = StructType(
    [
        StructField("message_id", StringType(), False),
        StructField("session_id", StringType(), False),
        StructField("role", StringType(), False),
        StructField("content", StringType(), False),
        StructField("sources", StringType(), True),
        StructField("token_usage", StringType(), True),
        StructField("latency_ms", IntegerType(), True),
        StructField("created_at", TimestampType(), False),
    ]
)

PIPELINE_RUNS_SCHEMA = StructType(
    [
        StructField("run_id", StringType(), False),
        StructField("started_at", TimestampType(), False),
        StructField("completed_at", TimestampType(), True),
        StructField("status", StringType(), False),
        StructField("documents_processed", IntegerType(), False),
        StructField("chunks_created", IntegerType(), False),
        StructField("error_message", StringType(), True),
    ]
)


class DeltaStore:
    """Wrapper around Delta Lake tables."""

    def __init__(self, spark: SparkSession, base_path: str | None = None):
        self.spark = spark
        self.base_path = base_path or settings.delta_lake_path

    def _table_path(self, name: str) -> str:
        return f"{self.base_path}/{name}"

    def _ensure_table(self, name: str, schema: StructType) -> None:
        path = self._table_path(name)
        try:
            self.spark.read.format("delta").load(path)
        except Exception:
            empty = self.spark.createDataFrame([], schema)
            empty.write.format("delta").mode("overwrite").save(path)
            logger.info("Created Delta table: %s", name)

    def init_tables(self) -> None:
        """Create all Delta Lake tables if they don't exist."""
        self._ensure_table("documents", DOCUMENTS_SCHEMA)
        self._ensure_table("chunks", CHUNKS_SCHEMA)
        self._ensure_table("chat_history", CHAT_HISTORY_SCHEMA)
        self._ensure_table("pipeline_runs", PIPELINE_RUNS_SCHEMA)

    def _read(self, name: str) -> DataFrame:
        return self.spark.read.format("delta").load(self._table_path(name))

    def _append(self, name: str, rows: list[dict[str, Any]], schema: StructType) -> None:
        df = self.spark.createDataFrame(rows, schema)
        df.write.format("delta").mode("append").save(self._table_path(name))

    # --- Documents ---

    def document_exists(self, content_hash: str) -> bool:
        df = self._read("documents").filter(F.col("content_hash") == content_hash)
        return df.count() > 0

    def save_document(self, doc: dict[str, Any]) -> None:
        self._append("documents", [doc], DOCUMENTS_SCHEMA)

    def list_documents(self) -> list[dict[str, Any]]:
        return [row.asDict() for row in self._read("documents").collect()]

    def count_documents(self) -> int:
        return self._read("documents").count()

    # --- Chunks ---

    def save_chunks(self, chunks: list[dict[str, Any]]) -> None:
        self._append("chunks", chunks, CHUNKS_SCHEMA)

    def get_chunks_by_ids(self, chunk_ids: list[str]) -> list[dict[str, Any]]:
        df = self._read("chunks").filter(F.col("chunk_id").isin(chunk_ids))
        return [row.asDict() for row in df.collect()]

    def get_chunks_for_document(self, document_id: str) -> list[dict[str, Any]]:
        df = (
            self._read("chunks")
            .filter(F.col("document_id") == document_id)
            .orderBy("chunk_index")
        )
        return [row.asDict() for row in df.collect()]

    def count_chunks(self) -> int:
        return self._read("chunks").count()

    def get_all_chunks_with_embeddings(self) -> list[dict[str, Any]]:
        df = self._read("chunks").filter(F.col("embedding").isNotNull())
        return [row.asDict() for row in df.collect()]

    # --- Chat History ---

    def save_chat_message(self, msg: dict[str, Any]) -> None:
        self._append("chat_history", [msg], CHAT_HISTORY_SCHEMA)

    def get_chat_history(self, session_id: str, limit: int = 20) -> list[dict[str, Any]]:
        df = (
            self._read("chat_history")
            .filter(F.col("session_id") == session_id)
            .orderBy(F.col("created_at").desc())
            .limit(limit)
        )
        rows = [row.asDict() for row in df.collect()]
        return list(reversed(rows))

    def get_query_logs(self, limit: int = 50) -> list[dict[str, Any]]:
        df = (
            self._read("chat_history")
            .filter(F.col("role") == "assistant")
            .orderBy(F.col("created_at").desc())
            .limit(limit)
        )
        return [row.asDict() for row in df.collect()]

    # --- Pipeline Runs ---

    def save_pipeline_run(self, run: dict[str, Any]) -> None:
        self._append("pipeline_runs", [run], PIPELINE_RUNS_SCHEMA)

    def update_pipeline_run(
        self,
        run_id: str,
        status: str,
        completed_at: datetime | None = None,
        documents_processed: int = 0,
        chunks_created: int = 0,
        error_message: str | None = None,
    ) -> None:
        path = self._table_path("pipeline_runs")
        from delta.tables import DeltaTable

        dt = DeltaTable.forPath(self.spark, path)
        updates: dict[str, Any] = {"status": F.lit(status)}
        if completed_at:
            updates["completed_at"] = F.lit(completed_at)
        if documents_processed:
            updates["documents_processed"] = F.lit(documents_processed)
        if chunks_created:
            updates["chunks_created"] = F.lit(chunks_created)
        if error_message is not None:
            updates["error_message"] = F.lit(error_message)
        dt.update(condition=F.col("run_id") == run_id, set=updates)

    def get_pipeline_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        df = (
            self._read("pipeline_runs").orderBy(F.col("started_at").desc()).limit(limit)
        )
        return [row.asDict() for row in df.collect()]

    def is_empty(self) -> bool:
        return self.count_documents() == 0
