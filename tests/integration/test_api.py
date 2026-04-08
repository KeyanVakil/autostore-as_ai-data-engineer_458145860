"""Integration tests for FastAPI endpoints.

These tests use httpx.AsyncClient with mocked dependencies (Spark, Delta, ChromaDB, LLM)
so they can run without external services.
"""

from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from warehouse_ai.api.dependencies import reset_dependencies
from warehouse_ai.api.main import app


@pytest.fixture(autouse=True)
def _reset_deps():
    """Reset cached dependencies before each test."""
    reset_dependencies()
    yield
    reset_dependencies()


@pytest.fixture()
def mock_services(mock_delta, mock_vector):
    """Patch all dependency injection points with mocks."""
    mock_agent = MagicMock()
    mock_agent.invoke.return_value = {
        "answer": "To replace the battery, power down the robot first.",
        "sources": [],
        "token_usage": {"prompt_tokens": 100, "completion_tokens": 30},
    }

    mock_spark = MagicMock()

    with (
        patch("warehouse_ai.api.dependencies.get_spark", return_value=mock_spark),
        patch("warehouse_ai.api.dependencies.get_delta", return_value=mock_delta),
        patch("warehouse_ai.api.dependencies.get_vector", return_value=mock_vector),
        patch("warehouse_ai.api.dependencies.get_agent", return_value=mock_agent),
        patch("warehouse_ai.api.main.get_spark", return_value=mock_spark),
        patch("warehouse_ai.api.main.get_delta", return_value=mock_delta),
        patch("warehouse_ai.api.main.get_vector", return_value=mock_vector),
    ):
        yield {
            "spark": mock_spark,
            "delta": mock_delta,
            "vector": mock_vector,
            "agent": mock_agent,
        }


@pytest.fixture()
async def client(mock_services):
    """Async test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    async def test_health_returns_200(self, client):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200

    async def test_health_response_schema(self, client):
        resp = await client.get("/api/v1/health")
        data = resp.json()
        assert "status" in data
        assert "spark" in data
        assert "chromadb" in data
        assert "llm_configured" in data


class TestDocumentsEndpoint:
    async def test_list_documents(self, client, mock_services):
        resp = await client.get("/api/v1/documents")
        assert resp.status_code == 200
        data = resp.json()
        assert "documents" in data
        assert "total" in data
        assert isinstance(data["documents"], list)

    async def test_list_documents_returns_count(self, client, mock_services):
        resp = await client.get("/api/v1/documents")
        data = resp.json()
        assert data["total"] == len(data["documents"])


class TestIngestEndpoint:
    async def test_ingest_rejects_unsupported_type(self, client, mock_services):
        file_content = b"col1,col2\nval1,val2"
        resp = await client.post(
            "/api/v1/ingest",
            files={"file": ("data.csv", io.BytesIO(file_content), "text/csv")},
        )
        assert resp.status_code == 400

    async def test_ingest_accepts_markdown(self, client, mock_services):
        with patch("warehouse_ai.api.routes.ingest.run_ingestion_pipeline", return_value="run-1"):
            file_content = b"# Test Document\n\nThis is a test."
            resp = await client.post(
                "/api/v1/ingest",
                files={"file": ("test.md", io.BytesIO(file_content), "text/markdown")},
            )
            assert resp.status_code == 202
            data = resp.json()
            assert data["filename"] == "test.md"
            assert data["status"] == "processing"


class TestSearchEndpoint:
    async def test_search_returns_results(self, client, mock_services):
        with patch("warehouse_ai.api.routes.search.vector_search") as mock_search:
            mock_search.return_value = [
                {
                    "chunk_id": "c-1",
                    "content": "Battery replacement procedure...",
                    "metadata": {"document_id": "doc-1"},
                    "relevance_score": 0.85,
                }
            ]
            with patch("warehouse_ai.api.routes.search.get_document_info") as mock_doc:
                mock_doc.return_value = {"title": "Maintenance Guide"}
                resp = await client.post(
                    "/api/v1/search",
                    json={"query": "battery replacement", "top_k": 5},
                )
                assert resp.status_code == 200
                data = resp.json()
                assert "results" in data
                assert len(data["results"]) == 1
                assert data["results"][0]["relevance_score"] == 0.85

    async def test_search_empty_results(self, client, mock_services):
        with patch("warehouse_ai.api.routes.search.vector_search", return_value=[]):
            resp = await client.post(
                "/api/v1/search",
                json={"query": "nonexistent topic"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["results"] == []


class TestChatSyncEndpoint:
    async def test_chat_sync_returns_answer(self, client, mock_services):
        resp = await client.post(
            "/api/v1/chat/sync",
            json={"message": "How do I replace a battery?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert "session_id" in data
        assert "sources" in data
        assert "latency_ms" in data
        assert len(data["message"]) > 0

    async def test_chat_sync_with_session_id(self, client, mock_services):
        resp = await client.post(
            "/api/v1/chat/sync",
            json={"message": "Hello", "session_id": "test-session-123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == "test-session-123"


class TestTeamsWebhook:
    async def test_teams_webhook_valid_message(self, client, mock_services):
        resp = await client.post(
            "/api/v1/teams/webhook",
            json={
                "type": "message",
                "text": "How do I reset a robot?",
                "from": {"id": "user-1", "name": "Operator"},
                "channelId": "msteams",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "message"
        assert "attachments" in data
        assert len(data["attachments"]) > 0
        assert data["attachments"][0]["contentType"] == "application/vnd.microsoft.card.adaptive"

    async def test_teams_webhook_invalid_type(self, client, mock_services):
        resp = await client.post(
            "/api/v1/teams/webhook",
            json={
                "type": "typing",
                "text": "",
                "from": {"id": "user-1", "name": "User"},
            },
        )
        assert resp.status_code == 400

    async def test_teams_webhook_empty_text(self, client, mock_services):
        resp = await client.post(
            "/api/v1/teams/webhook",
            json={
                "type": "message",
                "text": "   ",
                "from": {"id": "user-1", "name": "User"},
            },
        )
        assert resp.status_code == 400


class TestPipelineEndpoint:
    async def test_pipeline_runs_empty(self, client, mock_services):
        resp = await client.get("/api/v1/pipeline/runs")
        assert resp.status_code == 200
        data = resp.json()
        assert "runs" in data
        assert isinstance(data["runs"], list)

    async def test_pipeline_runs_with_data(self, client, mock_services):
        mock_services["delta"].get_pipeline_runs.return_value = [
            {
                "run_id": "run-1",
                "status": "success",
                "started_at": datetime.now(timezone.utc),
                "completed_at": datetime.now(timezone.utc),
                "documents_processed": 3,
                "chunks_created": 42,
                "error_message": None,
            }
        ]
        resp = await client.get("/api/v1/pipeline/runs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["runs"]) == 1
        assert data["runs"][0]["status"] == "success"
