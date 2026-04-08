"""PySpark document ingestion pipeline."""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from pyspark.sql import SparkSession

from warehouse_ai.config import settings
from warehouse_ai.pipeline.chunker import chunk_text
from warehouse_ai.pipeline.embedder import embed_texts
from warehouse_ai.pipeline.sync import sync_to_chromadb
from warehouse_ai.storage.delta import DeltaStore
from warehouse_ai.storage.vector import VectorStore

logger = logging.getLogger(__name__)


def extract_text(file_path: str) -> str:
    """Extract text from a file (PDF, markdown, or plain text)."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf(file_path)
    elif suffix in (".md", ".txt"):
        return path.read_text(encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def _extract_pdf(file_path: str) -> str:
    """Extract text from a PDF using PyMuPDF."""
    import fitz

    doc = fitz.open(file_path)
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts)


def ingest_file(
    file_path: str,
    spark: SparkSession,
    delta: DeltaStore,
    vector: VectorStore,
    run_id: str | None = None,
) -> dict:
    """Ingest a single document through the full pipeline.

    Returns metadata about the ingested document.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Extract text
    text = extract_text(file_path)
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

    # Check for duplicates
    if delta.document_exists(content_hash):
        logger.info("Document already ingested (hash match): %s", path.name)
        return {"filename": path.name, "status": "duplicate", "content_hash": content_hash}

    document_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # Chunk the document
    chunks = chunk_text(
        text,
        document_id=document_id,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        metadata={"filename": path.name, "file_type": path.suffix.lstrip(".")},
    )

    # Generate embeddings
    chunk_texts = [c["content"] for c in chunks]
    embeddings = embed_texts(chunk_texts)
    for i, chunk in enumerate(chunks):
        chunk["embedding"] = embeddings[i]

    # Derive title from filename
    title = path.stem.replace("_", " ").replace("-", " ").title()

    # Save document record
    doc_record = {
        "document_id": document_id,
        "filename": path.name,
        "content_hash": content_hash,
        "file_type": path.suffix.lstrip("."),
        "file_size_bytes": path.stat().st_size,
        "title": title,
        "ingested_at": now,
        "chunk_count": len(chunks),
        "status": "active",
    }
    delta.save_document(doc_record)

    # Save chunks
    delta.save_chunks(chunks)

    # Sync to ChromaDB
    sync_to_chromadb(delta, vector)

    logger.info(
        "Ingested %s: %d chunks, document_id=%s",
        path.name,
        len(chunks),
        document_id,
    )

    return {
        "document_id": document_id,
        "filename": path.name,
        "title": title,
        "chunk_count": len(chunks),
        "status": "ingested",
    }


def ingest_directory(
    directory: str,
    spark: SparkSession,
    delta: DeltaStore,
    vector: VectorStore,
) -> list[dict]:
    """Ingest all supported files from a directory."""
    dir_path = Path(directory)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    results = []
    for ext in ("*.md", "*.txt", "*.pdf"):
        for file_path in sorted(dir_path.glob(ext)):
            try:
                result = ingest_file(str(file_path), spark, delta, vector)
                results.append(result)
            except Exception as e:
                logger.error("Failed to ingest %s: %s", file_path.name, e)
                results.append({"filename": file_path.name, "status": "error", "error": str(e)})

    return results


def run_ingestion_pipeline(
    file_paths: list[str],
    spark: SparkSession,
    delta: DeltaStore,
    vector: VectorStore,
) -> str:
    """Run the full ingestion pipeline for a list of files.

    Creates a pipeline run record, processes files, and updates the run status.
    Returns the run_id.
    """
    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    delta.save_pipeline_run(
        {
            "run_id": run_id,
            "started_at": now,
            "completed_at": None,
            "status": "running",
            "documents_processed": 0,
            "chunks_created": 0,
            "error_message": None,
        }
    )

    total_docs = 0
    total_chunks = 0
    errors: list[str] = []

    for fp in file_paths:
        try:
            result = ingest_file(fp, spark, delta, vector, run_id=run_id)
            if result["status"] == "ingested":
                total_docs += 1
                total_chunks += result.get("chunk_count", 0)
        except Exception as e:
            logger.error("Pipeline error for %s: %s", fp, e)
            errors.append(f"{fp}: {e}")

    completed_at = datetime.now(timezone.utc)
    status = "success" if not errors else "failed"
    error_msg = "; ".join(errors) if errors else None

    delta.update_pipeline_run(
        run_id=run_id,
        status=status,
        completed_at=completed_at,
        documents_processed=total_docs,
        chunks_created=total_chunks,
        error_message=error_msg,
    )

    logger.info(
        "Pipeline run %s completed: %s (%d docs, %d chunks)",
        run_id,
        status,
        total_docs,
        total_chunks,
    )
    return run_id
