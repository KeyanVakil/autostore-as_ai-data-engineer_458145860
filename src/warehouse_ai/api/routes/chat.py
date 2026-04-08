"""Chat endpoints with streaming support."""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from langchain_core.messages import HumanMessage
from sse_starlette.sse import EventSourceResponse

from warehouse_ai.api.dependencies import get_agent, get_delta
from warehouse_ai.api.models import ChatRequest, ChatResponse, SourceReference, TokenUsage
from warehouse_ai.storage.delta import DeltaStore

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat")
async def chat(
    request: ChatRequest,
    agent=Depends(get_agent),
    delta: DeltaStore = Depends(get_delta),
):
    """Send a message to the RAG assistant. Returns SSE stream."""
    session_id = request.session_id or str(uuid.uuid4())
    start_time = time.time()

    # Save user message to chat history
    delta.save_chat_message(
        {
            "message_id": str(uuid.uuid4()),
            "session_id": session_id,
            "role": "user",
            "content": request.message,
            "sources": None,
            "token_usage": None,
            "latency_ms": None,
            "created_at": datetime.now(timezone.utc),
        }
    )

    # Load chat history for context
    history = delta.get_chat_history(session_id, limit=10)
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))

    # Run agent
    result = agent.invoke(
        {
            "messages": messages,
            "query": request.message,
            "session_id": session_id,
        }
    )

    latency_ms = int((time.time() - start_time) * 1000)
    answer = result.get("answer", "")
    sources_raw = result.get("sources", [])
    token_usage = result.get("token_usage", {})

    sources = [
        SourceReference(
            document_id=s.document_id,
            document_title=s.document_title,
            chunk_id=s.chunk_id,
            chunk_index=s.chunk_index,
            relevance_score=s.relevance_score,
            snippet=s.content[:200],
        )
        for s in sources_raw
    ]

    # Save assistant response
    delta.save_chat_message(
        {
            "message_id": str(uuid.uuid4()),
            "session_id": session_id,
            "role": "assistant",
            "content": answer,
            "sources": json.dumps([s.chunk_id for s in sources_raw]),
            "token_usage": json.dumps(token_usage),
            "latency_ms": latency_ms,
            "created_at": datetime.now(timezone.utc),
        }
    )

    async def event_generator():
        # Stream answer token-by-token (simulated chunking for SSE)
        words = answer.split(" ")
        for i, word in enumerate(words):
            token = word if i == 0 else " " + word
            yield {
                "event": "message",
                "data": json.dumps({"type": "token", "content": token}),
            }

        # Send sources
        yield {
            "event": "message",
            "data": json.dumps(
                {"type": "sources", "sources": [s.model_dump() for s in sources]}
            ),
        }

        # Send done signal
        yield {
            "event": "message",
            "data": json.dumps(
                {
                    "type": "done",
                    "session_id": session_id,
                    "latency_ms": latency_ms,
                    "token_usage": token_usage,
                }
            ),
        }

    return EventSourceResponse(event_generator())


@router.post("/chat/sync", response_model=ChatResponse)
async def chat_sync(
    request: ChatRequest,
    agent=Depends(get_agent),
    delta: DeltaStore = Depends(get_delta),
):
    """Non-streaming chat endpoint for simpler clients."""
    session_id = request.session_id or str(uuid.uuid4())
    start_time = time.time()

    delta.save_chat_message(
        {
            "message_id": str(uuid.uuid4()),
            "session_id": session_id,
            "role": "user",
            "content": request.message,
            "sources": None,
            "token_usage": None,
            "latency_ms": None,
            "created_at": datetime.now(timezone.utc),
        }
    )

    result = agent.invoke(
        {
            "messages": [HumanMessage(content=request.message)],
            "query": request.message,
            "session_id": session_id,
        }
    )

    latency_ms = int((time.time() - start_time) * 1000)
    answer = result.get("answer", "")
    sources_raw = result.get("sources", [])
    token_usage = result.get("token_usage", {})

    sources = [
        SourceReference(
            document_id=s.document_id,
            document_title=s.document_title,
            chunk_id=s.chunk_id,
            chunk_index=s.chunk_index,
            relevance_score=s.relevance_score,
            snippet=s.content[:200],
        )
        for s in sources_raw
    ]

    delta.save_chat_message(
        {
            "message_id": str(uuid.uuid4()),
            "session_id": session_id,
            "role": "assistant",
            "content": answer,
            "sources": json.dumps([s.chunk_id for s in sources_raw]),
            "token_usage": json.dumps(token_usage),
            "latency_ms": latency_ms,
            "created_at": datetime.now(timezone.utc),
        }
    )

    return ChatResponse(
        message=answer,
        session_id=session_id,
        sources=sources,
        latency_ms=latency_ms,
        token_usage=TokenUsage(**token_usage),
    )
