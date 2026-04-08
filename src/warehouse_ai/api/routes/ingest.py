"""Document upload and ingestion endpoints."""

from __future__ import annotations

import logging
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from warehouse_ai.api.dependencies import get_delta, get_spark, get_vector
from warehouse_ai.api.models import DocumentInfo, DocumentListResponse, IngestResponse
from warehouse_ai.config import settings
from warehouse_ai.pipeline.ingest import run_ingestion_pipeline
from warehouse_ai.storage.delta import DeltaStore

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ingest", response_model=IngestResponse, status_code=202)
async def ingest_document(
    file: UploadFile = File(...),
    spark=Depends(get_spark),
    delta: DeltaStore = Depends(get_delta),
    vector=Depends(get_vector),
):
    """Upload and ingest a document (PDF, markdown, or plain text)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".pdf", ".md", ".txt"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}. Supported: .pdf, .md, .txt",
        )

    # Save uploaded file
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_id = str(uuid.uuid4())
    dest = upload_dir / f"{file_id}{suffix}"

    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Run ingestion pipeline
    run_id = run_ingestion_pipeline([str(dest)], spark, delta, vector)

    # Get the document ID from the pipeline results
    docs = delta.list_documents()
    doc_id = docs[-1]["document_id"] if docs else file_id

    return IngestResponse(
        document_id=doc_id,
        filename=file.filename,
        status="processing",
        run_id=run_id,
    )


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(delta: DeltaStore = Depends(get_delta)):
    """List all ingested documents."""
    docs = delta.list_documents()
    return DocumentListResponse(
        documents=[DocumentInfo(**d) for d in docs],
        total=len(docs),
    )
