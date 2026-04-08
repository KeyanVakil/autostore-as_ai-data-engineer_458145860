"""Document upload and browser page."""

from __future__ import annotations

import streamlit as st

from components.common import api_get, api_post, render_status_bar

st.set_page_config(page_title="Documents - Warehouse AI", page_icon="🏭", layout="wide")
st.title("📄 Documents")
st.caption("Upload warehouse documentation and browse ingested files.")

render_status_bar()

# Upload section
st.subheader("Upload Document")
uploaded_file = st.file_uploader(
    "Choose a file to ingest",
    type=["pdf", "md", "txt"],
    help="Supported formats: PDF, Markdown (.md), Plain text (.txt)",
)

if uploaded_file is not None:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"**{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
    with col2:
        if st.button("Ingest", type="primary", use_container_width=True):
            with st.spinner("Uploading and processing..."):
                try:
                    resp = api_post(
                        "/ingest",
                        files={"file": (uploaded_file.name, uploaded_file, uploaded_file.type)},
                    )
                    if resp.status_code in (200, 202):
                        data = resp.json()
                        st.success(
                            f"Document **{data['filename']}** submitted for ingestion. "
                            f"Run ID: `{data['run_id'][:8]}...`"
                        )
                        st.rerun()
                    else:
                        st.error(f"Ingestion failed: {resp.text}")
                except Exception as e:
                    st.error(f"Error uploading document: {e}")

st.divider()

# Document list
st.subheader("Ingested Documents")

try:
    resp = api_get("/documents")
    if resp.status_code == 200:
        data = resp.json()
        documents = data.get("documents", [])
        total = data.get("total", 0)

        st.caption(f"{total} document{'s' if total != 1 else ''} in the knowledge base")

        if documents:
            for doc in documents:
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([3, 1, 1, 2])
                    with c1:
                        st.markdown(f"**{doc.get('title') or doc.get('filename', 'Untitled')}**")
                        st.caption(doc.get("filename", ""))
                    with c2:
                        st.metric("Chunks", doc.get("chunk_count", 0))
                    with c3:
                        status = doc.get("status", "unknown")
                        if status == "active":
                            st.success(status)
                        else:
                            st.warning(status)
                    with c4:
                        ingested = doc.get("ingested_at", "")
                        if ingested:
                            st.caption(f"Ingested: {ingested[:19]}")
                        st.caption(f"ID: `{doc.get('document_id', '')[:8]}...`")
        else:
            st.info(
                "No documents ingested yet. Upload a file above or wait for the sample "
                "data to be ingested on first startup."
            )
    else:
        st.error(f"Failed to load documents: {resp.status_code}")
except Exception as e:
    st.error(f"Could not load documents: {e}")
