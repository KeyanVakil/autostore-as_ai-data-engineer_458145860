"""Shared test fixtures."""

from __future__ import annotations

import os
import tempfile
from unittest.mock import MagicMock

import pytest


@pytest.fixture()
def sample_text() -> str:
    """A paragraph of sample warehouse documentation text."""
    return (
        "The AutoStore grid robot (R5) requires routine maintenance every 500 operating hours. "
        "To perform a battery replacement, first power down the robot using the controller panel. "
        "Disconnect the charging contacts and remove the four M4 screws securing the battery tray. "
        "Replace with a genuine AutoStore replacement battery (part number AS-BAT-R5-001). "
        "Reconnect the charging contacts and verify the LED indicator shows solid green before "
        "returning the robot to the grid. Always wear anti-static gloves during this procedure. "
        "If the LED indicator shows flashing red, consult the troubleshooting guide section 4.2. "
        "Battery performance degrades below 10C ambient temperature; ensure the warehouse "
        "climate control system maintains at least 15C in the grid area."
    )


@pytest.fixture()
def long_text() -> str:
    """A text long enough to require multiple chunks."""
    paragraph = (
        "Warehouse operations require careful coordination between automated systems and "
        "human operators. The grid structure houses bins stacked vertically, with robots "
        "navigating the top surface to retrieve and deliver bins to port stations. Each robot "
        "communicates with the central controller via a proprietary wireless protocol. "
        "Performance metrics are tracked continuously, including bin retrieval time, robot "
        "utilization rate, and order throughput per hour. Regular maintenance windows are "
        "scheduled weekly to inspect rails, clean contacts, and verify firmware versions. "
    )
    # Repeat to ensure it exceeds 500 tokens
    return (paragraph * 15).strip()


@pytest.fixture()
def tmp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture()
def mock_delta():
    """A mock DeltaStore for tests that don't need real Spark."""
    mock = MagicMock()
    mock.list_documents.return_value = [
        {
            "document_id": "doc-001",
            "filename": "robot_maintenance_guide.md",
            "content_hash": "abc123",
            "file_type": "md",
            "file_size_bytes": 4096,
            "title": "Robot Maintenance Guide",
            "ingested_at": "2026-04-07T10:00:00",
            "chunk_count": 12,
            "status": "active",
        }
    ]
    mock.is_empty.return_value = False
    mock.count_documents.return_value = 1
    mock.count_chunks.return_value = 12
    mock.get_pipeline_runs.return_value = []
    mock.get_chat_history.return_value = []
    return mock


@pytest.fixture()
def mock_vector():
    """A mock VectorStore for tests that don't need real ChromaDB."""
    mock = MagicMock()
    mock.heartbeat.return_value = True
    mock.count.return_value = 12
    mock.search.return_value = [
        {
            "chunk_id": "chunk-001",
            "content": "To replace the battery, first power down the robot...",
            "metadata": {"document_id": "doc-001"},
            "relevance_score": 0.85,
        }
    ]
    return mock
