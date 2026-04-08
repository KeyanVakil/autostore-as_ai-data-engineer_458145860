"""Text chunking logic with recursive character splitting."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

import tiktoken

logger = logging.getLogger(__name__)

_enc = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count tokens using the cl100k_base encoding."""
    return len(_enc.encode(text))


def chunk_text(
    text: str,
    document_id: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    metadata: dict | None = None,
) -> list[dict]:
    """Split text into chunks of approximately chunk_size tokens with overlap.

    Uses a recursive character-splitting strategy: first tries splitting on double
    newlines (paragraphs), then single newlines, then sentences, then words.
    """
    if not text.strip():
        return []

    separators = ["\n\n", "\n", ". ", " "]
    raw_chunks = _recursive_split(text, separators, chunk_size)

    # Merge small chunks and add overlap
    merged = _merge_with_overlap(raw_chunks, chunk_size, chunk_overlap)

    now = datetime.now(timezone.utc)
    results = []
    for i, chunk_text_str in enumerate(merged):
        token_count = count_tokens(chunk_text_str)
        results.append(
            {
                "chunk_id": str(uuid.uuid4()),
                "document_id": document_id,
                "chunk_index": i,
                "content": chunk_text_str,
                "token_count": token_count,
                "embedding": None,
                "metadata": str(metadata or {}),
                "created_at": now,
            }
        )

    logger.info(
        "Chunked document %s into %d chunks (avg %d tokens)",
        document_id,
        len(results),
        sum(c["token_count"] for c in results) // max(len(results), 1),
    )
    return results


def _recursive_split(text: str, separators: list[str], chunk_size: int) -> list[str]:
    """Recursively split text using progressively finer separators."""
    if count_tokens(text) <= chunk_size:
        return [text] if text.strip() else []

    if not separators:
        # Last resort: hard split by tokens
        return _hard_split(text, chunk_size)

    sep = separators[0]
    parts = text.split(sep)

    chunks: list[str] = []
    current = ""
    for part in parts:
        candidate = (current + sep + part) if current else part
        if count_tokens(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            if count_tokens(part) > chunk_size:
                chunks.extend(_recursive_split(part, separators[1:], chunk_size))
            else:
                current = part
                continue
            current = ""

    if current.strip():
        chunks.append(current)

    return chunks


def _hard_split(text: str, chunk_size: int) -> list[str]:
    """Split text by token count when no separator works."""
    tokens = _enc.encode(text)
    chunks = []
    for i in range(0, len(tokens), chunk_size):
        chunk_tokens = tokens[i : i + chunk_size]
        chunks.append(_enc.decode(chunk_tokens))
    return chunks


def _merge_with_overlap(chunks: list[str], chunk_size: int, overlap: int) -> list[str]:
    """Merge small chunks and add overlap between adjacent chunks."""
    if not chunks:
        return []

    # First pass: merge very small chunks
    merged: list[str] = []
    current = chunks[0]
    for chunk in chunks[1:]:
        candidate = current + "\n" + chunk
        if count_tokens(candidate) <= chunk_size:
            current = candidate
        else:
            merged.append(current)
            current = chunk
    merged.append(current)

    if overlap <= 0 or len(merged) <= 1:
        return merged

    # Second pass: add overlap from previous chunk
    result = [merged[0]]
    for i in range(1, len(merged)):
        prev_tokens = _enc.encode(merged[i - 1])
        overlap_text = _enc.decode(prev_tokens[-overlap:]) if len(prev_tokens) > overlap else ""
        if overlap_text:
            result.append(overlap_text.lstrip() + "\n" + merged[i])
        else:
            result.append(merged[i])

    return result
