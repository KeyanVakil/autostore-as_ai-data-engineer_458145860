"""Agent state schema for the LangGraph RAG agent."""

from __future__ import annotations

from typing import Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class SourceChunk(BaseModel):
    """A retrieved document chunk used as context."""

    chunk_id: str
    document_id: str
    document_title: str
    chunk_index: int
    content: str
    relevance_score: float


class AgentState(BaseModel):
    """State that flows through the LangGraph RAG agent."""

    messages: Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)
    query: str = ""
    reformulated_query: str = ""
    retrieved_chunks: list[SourceChunk] = Field(default_factory=list)
    has_relevant_context: bool = False
    answer: str = ""
    sources: list[SourceChunk] = Field(default_factory=list)
    token_usage: dict = Field(default_factory=dict)
    session_id: str = ""
