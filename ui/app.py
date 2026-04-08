"""AutoStore Warehouse Knowledge Assistant - Streamlit UI entry point."""

from __future__ import annotations

import streamlit as st

from components.common import check_backend_health, get_backend_url

st.set_page_config(
    page_title="Warehouse Knowledge Assistant",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🏭 AutoStore Warehouse Knowledge Assistant")
st.markdown(
    "AI-powered search and chat for warehouse operations documentation. "
    "Upload documents, ask questions, and get cited answers from your knowledge base."
)

# Sidebar navigation info
st.sidebar.markdown("### Navigation")
st.sidebar.markdown(
    "Use the pages in the sidebar to:\n"
    "- **Chat** with the AI assistant\n"
    "- **Documents** upload and browse\n"
    "- **Search** semantic document search\n"
    "- **Monitor** pipeline run history\n"
    "- **Teams** integration preview"
)

st.sidebar.divider()

# Backend health check
health = check_backend_health()

if health is None:
    st.error(
        "Could not connect to the backend. "
        f"Make sure the API is running at `{get_backend_url()}`."
    )
    st.info(
        "Start the full stack with:\n```bash\ndocker compose up --build\n```"
    )
    st.stop()

status = health.get("status", "unknown")
spark = health.get("spark", "unknown")
chroma = health.get("chromadb", "unknown")
llm_configured = health.get("llm_configured", False)

# Status indicators
col1, col2, col3, col4 = st.columns(4)

with col1:
    if status == "healthy":
        st.success("System: Healthy")
    else:
        st.warning(f"System: {status}")

with col2:
    if spark == "connected":
        st.success("Spark: Connected")
    else:
        st.error(f"Spark: {spark}")

with col3:
    if chroma == "connected":
        st.success("ChromaDB: Connected")
    else:
        st.error(f"ChromaDB: {chroma}")

with col4:
    if llm_configured:
        st.success("LLM: Configured")
    else:
        st.warning("LLM: No API key")

st.divider()

# Quick stats
st.subheader("Knowledge Base Overview")

try:
    from components.common import api_get

    docs_resp = api_get("/documents")
    if docs_resp.status_code == 200:
        docs_data = docs_resp.json()
        total_docs = docs_data.get("total", 0)
        documents = docs_data.get("documents", [])
        total_chunks = sum(d.get("chunk_count", 0) for d in documents)

        m1, m2, m3 = st.columns(3)
        m1.metric("Documents Ingested", total_docs)
        m2.metric("Total Chunks", f"{total_chunks:,}")
        m3.metric(
            "Latest Document",
            documents[-1]["filename"] if documents else "None",
        )
    else:
        st.info("No documents ingested yet. Go to the Documents page to upload files.")
except Exception:
    st.info("Could not load document statistics.")

st.divider()

# Getting started
st.subheader("Getting Started")
st.markdown(
    """
1. **Upload documents** -- Go to the *Documents* page and upload PDF, Markdown, or text files
   containing warehouse operations documentation.
2. **Ask questions** -- Use the *Chat* page to ask questions. The AI assistant retrieves
   relevant document sections and generates cited answers.
3. **Search directly** -- The *Search* page lets you run semantic queries and see matching
   document chunks with relevance scores.
4. **Monitor pipelines** -- The *Monitor* page shows ingestion pipeline history and system
   performance metrics.
"""
)

if not llm_configured:
    st.info(
        "Set the `OPENAI_API_KEY` environment variable to enable the full chat assistant. "
        "Without it, document ingestion and vector search work using a local embedding model, "
        "but chat responses are unavailable."
    )
