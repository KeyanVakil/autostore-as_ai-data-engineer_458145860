"""LangGraph agent nodes: retrieve, evaluate, generate."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from warehouse_ai.agent.state import AgentState, SourceChunk
from warehouse_ai.agent.tools import get_document_info, vector_search
from warehouse_ai.config import settings
from warehouse_ai.storage.delta import DeltaStore
from warehouse_ai.storage.vector import VectorStore

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a knowledgeable warehouse operations assistant for AutoStore automated warehouse systems. You help operators, technicians, and engineers find answers in their technical documentation, SOPs, incident reports, and training materials.

Rules:
- Answer based ONLY on the provided context. Do not make up information.
- Cite your sources using [document_title, chunk_index] format.
- If the context doesn't contain enough information to answer, say so honestly.
- Be concise but thorough. Use bullet points and structured formatting when helpful.
- For safety-related questions, always emphasize following proper procedures."""


def make_retrieve_node(delta: DeltaStore, vector: VectorStore):
    """Create a retrieval node that searches for relevant chunks."""

    def retrieve(state: AgentState) -> dict[str, Any]:
        query = state.reformulated_query or state.query
        results = vector_search(query, vector)

        chunks = []
        for r in results:
            doc_id = r.get("metadata", {}).get("document_id", "")
            doc_info = get_document_info(doc_id, delta) if doc_id else None
            doc_title = doc_info["title"] if doc_info else "Unknown"

            chunks.append(
                SourceChunk(
                    chunk_id=r["chunk_id"],
                    document_id=doc_id,
                    document_title=doc_title,
                    chunk_index=r.get("metadata", {}).get("chunk_index", 0),
                    content=r["content"],
                    relevance_score=r["relevance_score"],
                )
            )

        return {"retrieved_chunks": chunks}

    return retrieve


def evaluate_relevance(state: AgentState) -> dict[str, Any]:
    """Evaluate whether retrieved chunks are relevant enough to answer the query."""
    if not state.retrieved_chunks:
        return {"has_relevant_context": False}

    # Check if we have at least one chunk above a reasonable threshold
    max_score = max(c.relevance_score for c in state.retrieved_chunks)
    return {"has_relevant_context": max_score >= settings.similarity_threshold}


def make_generate_node(delta: DeltaStore):
    """Create a generation node that produces an answer from context."""

    def generate(state: AgentState) -> dict[str, Any]:
        if not settings.llm_configured:
            return {
                "answer": (
                    "LLM is not configured. Set the OPENAI_API_KEY environment variable "
                    "to enable full chat functionality. Retrieved context is available "
                    "in the sources section below."
                ),
                "sources": state.retrieved_chunks,
                "token_usage": {"prompt_tokens": 0, "completion_tokens": 0},
            }

        import openai

        client = openai.OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url or None,
        )

        # Build context string from retrieved chunks
        context_parts = []
        for chunk in state.retrieved_chunks:
            context_parts.append(
                f"[{chunk.document_title}, chunk {chunk.chunk_index}]:\n{chunk.content}"
            )
        context = "\n\n---\n\n".join(context_parts)

        # Build conversation history
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add chat history from state messages
        for msg in state.messages[:-1]:  # Exclude the current query
            if isinstance(msg, HumanMessage):
                messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                messages.append({"role": "assistant", "content": msg.content})

        # Add current query with context
        user_msg = f"""Context from warehouse documentation:

{context}

Question: {state.query}"""

        messages.append({"role": "user", "content": user_msg})

        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.1,
            max_tokens=1500,
        )

        answer = response.choices[0].message.content or ""
        usage = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
        }

        return {
            "answer": answer,
            "sources": state.retrieved_chunks,
            "token_usage": usage,
        }

    return generate


def generate_no_context(state: AgentState) -> dict[str, Any]:
    """Generate a response when no relevant context was found."""
    return {
        "answer": (
            "I couldn't find relevant information in the warehouse documentation to answer "
            "your question. Please try rephrasing your question, or make sure the relevant "
            "documents have been ingested into the system."
        ),
        "sources": [],
        "token_usage": {"prompt_tokens": 0, "completion_tokens": 0},
    }


def reformulate_query(state: AgentState) -> dict[str, Any]:
    """Reformulate the query for better retrieval.

    For now, uses the raw query. With an LLM configured, this would
    rewrite the query to improve retrieval quality.
    """
    if not settings.llm_configured:
        return {"reformulated_query": state.query}

    import openai

    client = openai.OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
    )

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Rewrite this question to be a better search query for finding "
                    "relevant warehouse operations documentation. Return ONLY the "
                    "rewritten query, nothing else."
                ),
            },
            {"role": "user", "content": state.query},
        ],
        temperature=0,
        max_tokens=100,
    )

    reformulated = response.choices[0].message.content or state.query
    return {"reformulated_query": reformulated.strip()}
