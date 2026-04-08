"""Tests for Pydantic API models."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from warehouse_ai.api.models import (
    ChatRequest,
    ChatResponse,
    DocumentInfo,
    DocumentListResponse,
    DocumentUpload,
    HealthResponse,
    IngestResponse,
    PipelineRunStatus,
    PipelineRunsResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
    SourceReference,
    TeamsActivity,
    TokenUsage,
)


class TestDocumentUpload:
    def test_valid_pdf(self):
        d = DocumentUpload(filename="test.pdf", content_type="application/pdf")
        assert d.filename == "test.pdf"

    def test_valid_markdown(self):
        d = DocumentUpload(filename="guide.md", content_type="text/markdown")
        assert d.content_type == "text/markdown"

    def test_invalid_content_type(self):
        with pytest.raises(Exception):
            DocumentUpload(filename="test.csv", content_type="text/csv")


class TestIngestResponse:
    def test_serialization(self):
        r = IngestResponse(
            document_id="doc-1", filename="test.pdf", status="processing", run_id="run-1"
        )
        data = r.model_dump()
        assert data["document_id"] == "doc-1"
        assert data["status"] == "processing"


class TestChatRequest:
    def test_minimal(self):
        r = ChatRequest(message="Hello")
        assert r.message == "Hello"
        assert r.session_id is None

    def test_with_session(self):
        r = ChatRequest(message="Hi", session_id="sess-123")
        assert r.session_id == "sess-123"


class TestSourceReference:
    def test_fields(self):
        s = SourceReference(
            document_id="doc-1",
            document_title="Guide",
            chunk_id="chunk-1",
            chunk_index=0,
            relevance_score=0.85,
            snippet="Some text...",
        )
        assert s.relevance_score == 0.85
        assert s.document_title == "Guide"


class TestTokenUsage:
    def test_defaults(self):
        t = TokenUsage()
        assert t.prompt_tokens == 0
        assert t.completion_tokens == 0

    def test_with_values(self):
        t = TokenUsage(prompt_tokens=100, completion_tokens=50)
        assert t.prompt_tokens == 100


class TestChatResponse:
    def test_full_response(self):
        r = ChatResponse(
            message="The procedure is...",
            session_id="sess-1",
            sources=[
                SourceReference(
                    document_id="doc-1",
                    document_title="Guide",
                    chunk_id="chunk-1",
                    chunk_index=0,
                    relevance_score=0.9,
                    snippet="text",
                )
            ],
            latency_ms=450,
            token_usage=TokenUsage(prompt_tokens=200, completion_tokens=80),
        )
        assert len(r.sources) == 1
        assert r.latency_ms == 450


class TestSearchRequest:
    def test_defaults(self):
        r = SearchRequest(query="battery replacement")
        assert r.top_k == 5
        assert r.min_score == 0.3
        assert r.filters is None

    def test_with_filters(self):
        r = SearchRequest(query="test", filters={"file_type": "pdf"})
        assert r.filters["file_type"] == "pdf"


class TestSearchResult:
    def test_fields(self):
        r = SearchResult(
            chunk_id="c-1",
            document_title="Maintenance Guide",
            content="Replace the battery...",
            relevance_score=0.87,
        )
        assert r.relevance_score == 0.87


class TestSearchResponse:
    def test_empty(self):
        r = SearchResponse(results=[])
        assert r.results == []

    def test_with_results(self):
        r = SearchResponse(
            results=[
                SearchResult(
                    chunk_id="c-1",
                    document_title="Guide",
                    content="text",
                    relevance_score=0.5,
                )
            ]
        )
        assert len(r.results) == 1


class TestTeamsActivity:
    def test_from_alias(self):
        """The 'from' field must be provided via the alias since 'from' is a Python keyword."""
        activity = TeamsActivity(
            type="message",
            text="Hello bot",
            **{"from": {"id": "user-1", "name": "Test User"}},
            channelId="msteams",
        )
        assert activity.from_ == {"id": "user-1", "name": "Test User"}
        assert activity.type == "message"

    def test_populate_by_name(self):
        """TeamsActivity supports populate_by_name so from_ works too."""
        activity = TeamsActivity(
            type="message",
            text="Hi",
            from_={"id": "u1", "name": "User"},
        )
        assert activity.from_["name"] == "User"

    def test_channel_id_optional(self):
        activity = TeamsActivity(
            type="message",
            text="Test",
            from_={"id": "u1", "name": "User"},
        )
        assert activity.channel_id is None

    def test_serialization_uses_alias(self):
        activity = TeamsActivity(
            type="message",
            text="Hi",
            from_={"id": "u1", "name": "User"},
        )
        data = activity.model_dump(by_alias=True)
        assert "from" in data
        assert "from_" not in data


class TestPipelineRunStatus:
    def test_valid_run(self):
        now = datetime.now(timezone.utc)
        r = PipelineRunStatus(
            run_id="run-1",
            status="success",
            started_at=now,
            completed_at=now,
            documents_processed=3,
            chunks_created=42,
        )
        assert r.status == "success"
        assert r.error_message is None

    def test_failed_run(self):
        now = datetime.now(timezone.utc)
        r = PipelineRunStatus(
            run_id="run-2",
            status="failed",
            started_at=now,
            completed_at=now,
            documents_processed=0,
            chunks_created=0,
            error_message="Spark OOM",
        )
        assert r.error_message == "Spark OOM"

    def test_invalid_status(self):
        with pytest.raises(Exception):
            PipelineRunStatus(
                run_id="run-3",
                status="cancelled",  # not in Literal
                started_at=datetime.now(timezone.utc),
                completed_at=None,
                documents_processed=0,
                chunks_created=0,
            )


class TestPipelineRunsResponse:
    def test_empty(self):
        r = PipelineRunsResponse(runs=[])
        assert r.runs == []


class TestDocumentInfo:
    def test_fields(self):
        d = DocumentInfo(
            document_id="doc-1",
            filename="test.md",
            title="Test Document",
            chunk_count=5,
            ingested_at=datetime.now(timezone.utc),
            status="active",
        )
        assert d.title == "Test Document"


class TestDocumentListResponse:
    def test_total_matches(self):
        r = DocumentListResponse(documents=[], total=0)
        assert r.total == 0


class TestHealthResponse:
    def test_healthy(self):
        r = HealthResponse(
            status="healthy",
            spark="connected",
            chromadb="connected",
            llm_configured=True,
        )
        assert r.status == "healthy"

    def test_degraded(self):
        r = HealthResponse(
            status="degraded",
            spark="connected",
            chromadb="error",
            llm_configured=False,
        )
        assert r.llm_configured is False
