"""Tests for the text chunking logic."""

from __future__ import annotations

import uuid

import pytest

from warehouse_ai.pipeline.chunker import (
    _hard_split,
    _merge_with_overlap,
    _recursive_split,
    chunk_text,
    count_tokens,
)


class TestCountTokens:
    """Token counting utility."""

    def test_empty_string(self):
        assert count_tokens("") == 0

    def test_single_word(self):
        assert count_tokens("hello") >= 1

    def test_consistent_results(self):
        text = "The quick brown fox jumps over the lazy dog."
        assert count_tokens(text) == count_tokens(text)

    def test_longer_text_more_tokens(self):
        short = "Hello"
        long = "Hello world, this is a longer sentence with many more tokens."
        assert count_tokens(long) > count_tokens(short)


class TestChunkText:
    """Main chunk_text function."""

    def test_empty_text_returns_empty(self):
        result = chunk_text("", document_id="doc-1")
        assert result == []

    def test_whitespace_only_returns_empty(self):
        result = chunk_text("   \n\n  ", document_id="doc-1")
        assert result == []

    def test_short_text_single_chunk(self):
        result = chunk_text("Hello world.", document_id="doc-1", chunk_size=500)
        assert len(result) == 1
        assert result[0]["content"] == "Hello world."
        assert result[0]["document_id"] == "doc-1"
        assert result[0]["chunk_index"] == 0

    def test_chunk_has_required_fields(self):
        result = chunk_text("Test content.", document_id="doc-1")
        chunk = result[0]
        assert "chunk_id" in chunk
        assert "document_id" in chunk
        assert "chunk_index" in chunk
        assert "content" in chunk
        assert "token_count" in chunk
        assert "embedding" in chunk
        assert "metadata" in chunk
        assert "created_at" in chunk

    def test_chunk_id_is_valid_uuid(self):
        result = chunk_text("Test content.", document_id="doc-1")
        uuid.UUID(result[0]["chunk_id"])  # raises if invalid

    def test_embedding_is_none(self):
        result = chunk_text("Some text.", document_id="doc-1")
        assert result[0]["embedding"] is None

    def test_token_count_matches(self):
        text = "This is a test sentence for token counting."
        result = chunk_text(text, document_id="doc-1")
        assert result[0]["token_count"] == count_tokens(text)

    def test_long_text_produces_multiple_chunks(self, long_text: str):
        result = chunk_text(long_text, document_id="doc-1", chunk_size=100, chunk_overlap=10)
        assert len(result) > 1

    def test_chunk_indices_sequential(self, long_text: str):
        result = chunk_text(long_text, document_id="doc-1", chunk_size=100, chunk_overlap=10)
        indices = [c["chunk_index"] for c in result]
        assert indices == list(range(len(result)))

    def test_all_chunks_have_same_document_id(self, long_text: str):
        result = chunk_text(long_text, document_id="doc-42", chunk_size=100)
        assert all(c["document_id"] == "doc-42" for c in result)

    def test_metadata_preserved(self):
        meta = {"section": "Chapter 1", "page": 5}
        result = chunk_text("Test.", document_id="doc-1", metadata=meta)
        assert result[0]["metadata"] == str(meta)

    def test_default_metadata_is_empty_dict_string(self):
        result = chunk_text("Test.", document_id="doc-1")
        assert result[0]["metadata"] == "{}"

    def test_chunk_size_respected(self, long_text: str):
        chunk_size = 100
        result = chunk_text(
            long_text, document_id="doc-1", chunk_size=chunk_size, chunk_overlap=0
        )
        for chunk in result:
            # Allow some tolerance since merge can slightly exceed target
            assert chunk["token_count"] <= chunk_size * 1.5

    def test_overlap_creates_redundancy(self, long_text: str):
        no_overlap = chunk_text(
            long_text, document_id="doc-1", chunk_size=100, chunk_overlap=0
        )
        with_overlap = chunk_text(
            long_text, document_id="doc-1", chunk_size=100, chunk_overlap=20
        )
        # With overlap, total content should be more (due to repeated text)
        total_no = sum(len(c["content"]) for c in no_overlap)
        total_with = sum(len(c["content"]) for c in with_overlap)
        assert total_with >= total_no


class TestRecursiveSplit:
    """Internal _recursive_split function."""

    def test_short_text_not_split(self):
        result = _recursive_split("Hello world.", ["\n\n", "\n", ". ", " "], 500)
        assert len(result) == 1

    def test_splits_on_paragraph_boundary(self):
        text = "Paragraph one.\n\nParagraph two."
        result = _recursive_split(text, ["\n\n", "\n", ". ", " "], 20)
        assert len(result) >= 2

    def test_empty_text(self):
        result = _recursive_split("", ["\n\n"], 100)
        assert result == []

    def test_falls_through_separators(self):
        # A single long line with no paragraph breaks but with spaces
        text = "word " * 200
        result = _recursive_split(text.strip(), ["\n\n", "\n", ". ", " "], 50)
        assert len(result) > 1


class TestHardSplit:
    """Internal _hard_split for when separators fail."""

    def test_splits_by_token_count(self):
        text = "a " * 100
        result = _hard_split(text.strip(), 20)
        assert len(result) > 1

    def test_short_text_single_chunk(self):
        result = _hard_split("Hello", 500)
        assert len(result) == 1


class TestMergeWithOverlap:
    """Internal _merge_with_overlap function."""

    def test_empty_input(self):
        assert _merge_with_overlap([], 100, 10) == []

    def test_single_chunk(self):
        result = _merge_with_overlap(["Hello world."], 100, 10)
        assert result == ["Hello world."]

    def test_no_overlap(self):
        chunks = ["Chunk one.", "Chunk two."]
        result = _merge_with_overlap(chunks, 5, 0)
        assert len(result) == 2

    def test_small_chunks_merged(self):
        # Two tiny chunks should merge if combined size <= chunk_size
        chunks = ["Hi.", "Bye."]
        result = _merge_with_overlap(chunks, 500, 0)
        assert len(result) == 1
        assert "Hi." in result[0]
        assert "Bye." in result[0]
