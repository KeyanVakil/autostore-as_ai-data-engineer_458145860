"""Pydantic models for the API layer."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class DocumentUpload(BaseModel):
    filename: str
    content_type: Literal["application/pdf", "text/markdown", "text/plain"]


class IngestResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    run_id: str


class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    title: str | None
    chunk_count: int
    ingested_at: datetime
    status: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo]
    total: int


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class SourceReference(BaseModel):
    document_id: str
    document_title: str
    chunk_id: str
    chunk_index: int
    relevance_score: float
    snippet: str


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0


class ChatResponse(BaseModel):
    message: str
    session_id: str
    sources: list[SourceReference]
    latency_ms: int
    token_usage: TokenUsage


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    min_score: float = 0.3
    filters: dict[str, Any] | None = None


class SearchResult(BaseModel):
    chunk_id: str
    document_title: str
    content: str
    relevance_score: float


class SearchResponse(BaseModel):
    results: list[SearchResult]


class TeamsActivity(BaseModel):
    type: str
    text: str
    from_: dict = Field(alias="from")
    channel_id: str | None = Field(default=None, alias="channelId")

    model_config = {"populate_by_name": True}


class PipelineRunStatus(BaseModel):
    run_id: str
    status: Literal["running", "success", "failed"]
    started_at: datetime
    completed_at: datetime | None
    documents_processed: int
    chunks_created: int
    error_message: str | None = None


class PipelineRunsResponse(BaseModel):
    runs: list[PipelineRunStatus]


class HealthResponse(BaseModel):
    status: str
    spark: str
    chromadb: str
    llm_configured: bool
