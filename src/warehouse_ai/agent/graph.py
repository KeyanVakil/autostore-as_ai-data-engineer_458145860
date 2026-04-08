"""LangGraph agent definition: the RAG workflow graph."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from warehouse_ai.agent.nodes import (
    evaluate_relevance,
    generate_no_context,
    make_generate_node,
    make_retrieve_node,
    reformulate_query,
)
from warehouse_ai.agent.state import AgentState
from warehouse_ai.storage.delta import DeltaStore
from warehouse_ai.storage.vector import VectorStore


def _route_after_eval(state: AgentState) -> str:
    """Route based on whether relevant context was found."""
    if state.has_relevant_context:
        return "generate"
    return "no_context"


def build_rag_graph(delta: DeltaStore, vector: VectorStore) -> StateGraph:
    """Build the LangGraph RAG agent graph.

    Flow: reformulate -> retrieve -> evaluate -> generate (or no_context)
    """
    retrieve_node = make_retrieve_node(delta, vector)
    generate_node = make_generate_node(delta)

    graph = StateGraph(AgentState)

    graph.add_node("reformulate", reformulate_query)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("evaluate", evaluate_relevance)
    graph.add_node("generate", generate_node)
    graph.add_node("no_context", generate_no_context)

    graph.set_entry_point("reformulate")
    graph.add_edge("reformulate", "retrieve")
    graph.add_edge("retrieve", "evaluate")
    graph.add_conditional_edges(
        "evaluate",
        _route_after_eval,
        {"generate": "generate", "no_context": "no_context"},
    )
    graph.add_edge("generate", END)
    graph.add_edge("no_context", END)

    return graph


def create_rag_agent(delta: DeltaStore, vector: VectorStore):
    """Create a compiled LangGraph RAG agent."""
    graph = build_rag_graph(delta, vector)
    return graph.compile()
