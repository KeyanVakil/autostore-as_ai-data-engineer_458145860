"""Chat interface page -- talk to the warehouse knowledge assistant."""

from __future__ import annotations

import json
import uuid

import requests
import streamlit as st

from components.common import (
    api_post,
    format_latency,
    get_backend_url,
    render_source_card,
    render_status_bar,
)

st.set_page_config(page_title="Chat - Warehouse AI", page_icon="🏭", layout="wide")
st.title("💬 Chat Assistant")
st.caption("Ask questions about warehouse operations and get cited answers from your documents.")

render_status_bar()

# Session management
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar controls
with st.sidebar:
    st.subheader("Session")
    if st.button("New conversation", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
    st.caption(f"Session: `{st.session_state.session_id[:8]}...`")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander(f"Sources ({len(msg['sources'])})"):
                for src in msg["sources"]:
                    render_source_card(src)
        if msg.get("latency_ms"):
            st.caption(f"Response time: {format_latency(msg['latency_ms'])}")

# Chat input
if prompt := st.chat_input("Ask about warehouse operations..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get assistant response via streaming endpoint
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        sources_placeholder = st.empty()
        status_placeholder = st.empty()

        full_response = ""
        sources = []
        latency_ms = 0

        try:
            resp = requests.post(
                f"{get_backend_url()}/api/v1/chat",
                json={
                    "message": prompt,
                    "session_id": st.session_state.session_id,
                },
                stream=True,
                timeout=120,
            )
            resp.raise_for_status()

            for line in resp.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data: "):
                    continue
                data = json.loads(line[6:])
                event_type = data.get("type", "")

                if event_type == "token":
                    full_response += data.get("content", "")
                    message_placeholder.markdown(full_response + "▌")

                elif event_type == "sources":
                    sources = data.get("sources", [])

                elif event_type == "done":
                    latency_ms = data.get("latency_ms", 0)

            message_placeholder.markdown(full_response)

            if sources:
                with sources_placeholder.expander(f"Sources ({len(sources)})"):
                    for src in sources:
                        render_source_card(src)

            if latency_ms:
                status_placeholder.caption(
                    f"Response time: {format_latency(latency_ms)}"
                )

        except requests.ConnectionError:
            full_response = "Could not connect to the backend. Is the API running?"
            message_placeholder.error(full_response)
        except requests.HTTPError as e:
            full_response = f"Backend error: {e.response.status_code}"
            message_placeholder.error(full_response)
        except Exception as e:
            full_response = f"Error: {e}"
            message_placeholder.error(full_response)

        # Store assistant message
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": full_response,
                "sources": sources,
                "latency_ms": latency_ms,
            }
        )
