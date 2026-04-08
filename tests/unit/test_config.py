"""Tests for application configuration."""

from __future__ import annotations

import os

import pytest

from warehouse_ai.config import Settings


class TestSettings:
    """Verify Settings loads defaults and respects environment overrides."""

    def test_default_values(self):
        s = Settings()
        assert s.llm_model == "gpt-4o-mini"
        assert s.embedding_model == "all-MiniLM-L6-v2"
        assert s.chunk_size == 500
        assert s.chunk_overlap == 50
        assert s.embedding_dimension == 384
        assert s.retrieval_top_k == 5
        assert s.similarity_threshold == 0.3
        assert s.chroma_port == 8100
        assert s.chroma_collection == "warehouse_chunks"

    def test_llm_not_configured_by_default(self):
        s = Settings()
        assert s.llm_configured is False

    def test_llm_configured_with_key(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-12345")
        s = Settings()
        assert s.llm_configured is True

    def test_env_override_chunk_size(self, monkeypatch):
        monkeypatch.setenv("CHUNK_SIZE", "1000")
        s = Settings()
        assert s.chunk_size == 1000

    def test_env_override_chroma_host(self, monkeypatch):
        monkeypatch.setenv("CHROMA_HOST", "my-chroma-server")
        s = Settings()
        assert s.chroma_host == "my-chroma-server"

    def test_sample_data_dir_is_absolute(self):
        s = Settings()
        assert os.path.isabs(s.sample_data_dir)

    def test_auto_ingest_sample_default_true(self):
        s = Settings()
        assert s.auto_ingest_sample is True

    def test_delta_lake_path_default(self):
        s = Settings()
        assert s.delta_lake_path == "/data/delta"

    def test_upload_dir_default(self):
        s = Settings()
        assert s.upload_dir == "/data/uploads"
