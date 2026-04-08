"""Semantic search explorer page."""

from __future__ import annotations

import streamlit as st

from components.common import api_post, render_source_card, render_status_bar

st.set_page_config(page_title="Search - Warehouse AI", page_icon="🏭", layout="wide")
st.title("🔍 Search Documents")
st.caption("Run semantic queries against the document knowledge base and explore matching chunks.")

render_status_bar()

# Search controls
with st.form("search_form"):
    query = st.text_input(
        "Search query",
        placeholder="e.g., battery replacement procedure for grid robots",
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        top_k = st.slider("Results to return", min_value=1, max_value=20, value=5)
    with col2:
        min_score = st.slider(
            "Minimum relevance", min_value=0.0, max_value=1.0, value=0.3, step=0.05
        )
    with col3:
        st.markdown("&nbsp;")  # spacer
        submitted = st.form_submit_button("Search", type="primary", use_container_width=True)

if submitted and query:
    with st.spinner("Searching..."):
        try:
            resp = api_post(
                "/search",
                json={"query": query, "top_k": top_k, "min_score": min_score},
            )
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])

                st.subheader(f"Results ({len(results)})")

                if results:
                    for i, result in enumerate(results, 1):
                        with st.container(border=True):
                            score = result.get("relevance_score", 0)
                            title = result.get("document_title", "Unknown")

                            header_col, score_col = st.columns([4, 1])
                            with header_col:
                                st.markdown(f"**{i}. {title}**")
                            with score_col:
                                color = (
                                    "green" if score > 0.7
                                    else "orange" if score > 0.4
                                    else "red"
                                )
                                st.markdown(f":{color}[**{score:.0%}**]")

                            content = result.get("content", "")
                            st.text(content[:500] + ("..." if len(content) > 500 else ""))
                            st.caption(f"Chunk ID: `{result.get('chunk_id', '')[:8]}...`")
                else:
                    st.info(
                        "No results found above the minimum relevance threshold. "
                        "Try broadening your query or lowering the minimum score."
                    )
            else:
                st.error(f"Search failed: {resp.status_code} - {resp.text}")
        except Exception as e:
            st.error(f"Search error: {e}")
elif submitted:
    st.warning("Please enter a search query.")
