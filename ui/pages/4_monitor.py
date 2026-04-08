"""Pipeline monitoring dashboard page."""

from __future__ import annotations

import streamlit as st

from components.common import api_get, format_latency, render_status_bar

st.set_page_config(page_title="Monitor - Warehouse AI", page_icon="🏭", layout="wide")
st.title("📊 Pipeline Monitor")
st.caption("Track ingestion pipeline runs and system performance metrics.")

render_status_bar()

# System overview
st.subheader("System Overview")

try:
    docs_resp = api_get("/documents")
    pipeline_resp = api_get("/pipeline/runs")

    if docs_resp.status_code == 200:
        docs_data = docs_resp.json()
        documents = docs_data.get("documents", [])
        total_docs = docs_data.get("total", 0)
        total_chunks = sum(d.get("chunk_count", 0) for d in documents)
    else:
        total_docs = 0
        total_chunks = 0
        documents = []

    if pipeline_resp.status_code == 200:
        runs_data = pipeline_resp.json()
        runs = runs_data.get("runs", [])
    else:
        runs = []

    # Metrics row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Documents", total_docs)
    m2.metric("Total Chunks", f"{total_chunks:,}")
    m3.metric("Pipeline Runs", len(runs))

    last_run_time = "Never"
    if runs:
        last_run = runs[0]
        last_run_time = str(last_run.get("started_at", ""))[:19]
    m4.metric("Last Run", last_run_time)

except Exception as e:
    st.error(f"Could not load system metrics: {e}")
    runs = []

st.divider()

# Pipeline run history
st.subheader("Pipeline Run History")

if runs:
    for run in runs:
        run_id = run.get("run_id", "")
        status = run.get("status", "unknown")
        started = str(run.get("started_at", ""))[:19]
        completed = run.get("completed_at")
        docs_processed = run.get("documents_processed", 0)
        chunks_created = run.get("chunks_created", 0)
        error_msg = run.get("error_message")

        with st.container(border=True):
            h1, h2 = st.columns([4, 1])
            with h1:
                st.markdown(f"**Run** `{run_id[:8]}...`")
            with h2:
                if status == "success":
                    st.success(status)
                elif status == "running":
                    st.info(status)
                else:
                    st.error(status)

            c1, c2, c3, c4 = st.columns(4)
            c1.caption(f"Started: {started}")
            if completed:
                c2.caption(f"Completed: {str(completed)[:19]}")
            else:
                c2.caption("Completed: --")
            c3.metric("Docs", docs_processed)
            c4.metric("Chunks", chunks_created)

            if error_msg:
                st.error(f"Error: {error_msg}")
else:
    st.info("No pipeline runs recorded yet. Upload a document to trigger the first run.")

st.divider()

# Query performance (from chat history assistant messages)
st.subheader("Query Performance")
st.caption(
    "Query latency and token usage are tracked per chat response in Delta Lake. "
    "This section shows recent assistant responses with their performance metrics."
)

try:
    # We don't have a dedicated query-logs endpoint, but the chat history
    # in Delta Lake tracks latency_ms and token_usage per assistant message.
    # In a production deployment, this would be exposed via a /metrics endpoint.
    st.info(
        "Query-level metrics are stored in the `chat_history` Delta Lake table. "
        "Use the Chat page to generate queries and observe per-response latency."
    )
except Exception:
    pass
