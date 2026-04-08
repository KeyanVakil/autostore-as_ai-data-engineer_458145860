"""FastAPI application with lifespan management."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from warehouse_ai.api.dependencies import get_delta, get_spark, get_vector
from warehouse_ai.api.models import HealthResponse
from warehouse_ai.api.routes import chat, ingest, pipeline, search, teams
from warehouse_ai.config import settings
from warehouse_ai.pipeline.ingest import ingest_directory

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init tables, auto-ingest sample data if empty."""
    logger.info("Starting Warehouse AI backend...")

    spark = get_spark()
    delta = get_delta()
    vector = get_vector()

    # Auto-ingest sample documents on first run
    if settings.auto_ingest_sample and delta.is_empty():
        sample_dir = Path(settings.sample_data_dir)
        if sample_dir.is_dir():
            logger.info("First run detected — ingesting sample documents from %s", sample_dir)
            results = ingest_directory(str(sample_dir), spark, delta, vector)
            ingested = sum(1 for r in results if r.get("status") == "ingested")
            logger.info("Ingested %d sample documents", ingested)
        else:
            logger.warning("Sample data directory not found: %s", sample_dir)

    logger.info("Backend ready")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="AutoStore Warehouse Knowledge Assistant",
    description="AI-powered RAG system for warehouse operations documentation",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(ingest.router, prefix="/api/v1", tags=["ingest"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(teams.router, prefix="/api/v1", tags=["teams"])
app.include_router(pipeline.router, prefix="/api/v1", tags=["pipeline"])


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """System health check."""
    spark_status = "connected"
    try:
        get_spark()
    except Exception:
        spark_status = "error"

    chroma_status = "connected"
    try:
        v = get_vector()
        if not v.heartbeat():
            chroma_status = "error"
    except Exception:
        chroma_status = "error"

    status = "healthy" if spark_status == "connected" and chroma_status == "connected" else "degraded"

    return HealthResponse(
        status=status,
        spark=spark_status,
        chromadb=chroma_status,
        llm_configured=settings.llm_configured,
    )
