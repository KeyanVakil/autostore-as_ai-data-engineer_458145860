"""Shared UI components for the Streamlit application."""

from __future__ import annotations

import os

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def get_backend_url() -> str:
    """Return the configured backend URL."""
    return BACKEND_URL


def api_get(path: str, **kwargs) -> requests.Response:
    """Make a GET request to the backend API."""
    return requests.get(f"{BACKEND_URL}/api/v1{path}", timeout=30, **kwargs)


def api_post(path: str, **kwargs) -> requests.Response:
    """Make a POST request to the backend API."""
    return requests.post(f"{BACKEND_URL}/api/v1{path}", timeout=60, **kwargs)


def check_backend_health() -> dict | None:
    """Check if the backend is healthy. Returns health data or None on failure."""
    try:
        resp = api_get("/health")
        if resp.status_code == 200:
            return resp.json()
    except requests.ConnectionError:
        pass
    return None


def render_header(title: str, icon: str = "") -> None:
    """Render a consistent page header."""
    st.set_page_config(
        page_title=f"{title} - Warehouse AI",
        page_icon="🏭",
        layout="wide",
    )
    st.title(f"{icon} {title}" if icon else title)


def render_status_bar() -> None:
    """Render a compact status bar showing backend health."""
    health = check_backend_health()
    if health is None:
        st.sidebar.error("Backend offline")
        return

    status = health.get("status", "unknown")
    spark = health.get("spark", "unknown")
    chroma = health.get("chromadb", "unknown")
    llm = health.get("llm_configured", False)

    if status == "healthy":
        st.sidebar.success("Backend: healthy")
    else:
        st.sidebar.warning(f"Backend: {status}")

    cols = st.sidebar.columns(3)
    cols[0].metric("Spark", spark)
    cols[1].metric("ChromaDB", chroma)
    cols[2].metric("LLM", "ready" if llm else "no key")


def render_source_card(source: dict) -> None:
    """Render a source citation card."""
    score = source.get("relevance_score", 0)
    title = source.get("document_title", "Unknown")
    snippet = source.get("snippet", source.get("content", ""))

    score_color = "green" if score > 0.7 else "orange" if score > 0.4 else "red"
    st.markdown(
        f"**{title}** &nbsp; "
        f":{score_color}[{score:.0%} relevance]"
    )
    st.caption(snippet[:300] + ("..." if len(snippet) > 300 else ""))


def format_latency(ms: int) -> str:
    """Format milliseconds into a human-readable string."""
    if ms < 1000:
        return f"{ms}ms"
    return f"{ms / 1000:.1f}s"
