"""Teams integration preview page -- simulates sending messages via the Teams webhook."""

from __future__ import annotations

import json

import streamlit as st

from components.common import api_post, render_status_bar

st.set_page_config(page_title="Teams Preview - Warehouse AI", page_icon="🏭", layout="wide")
st.title("💼 Teams Integration Preview")
st.caption(
    "Simulate Microsoft Teams bot interactions. Messages are sent through the same "
    "RAG pipeline via the Teams webhook endpoint."
)

render_status_bar()

# Info panel
with st.expander("How Teams integration works"):
    st.markdown(
        """
The backend exposes a `POST /api/v1/teams/webhook` endpoint that accepts
Microsoft Teams bot framework activity messages. When a user sends a message
in a Teams channel, the bot:

1. Receives the activity message (type, text, sender info)
2. Routes the message through the LangGraph RAG agent
3. Returns a Teams Adaptive Card with the answer and source citations

This page lets you preview that interaction without a real Teams setup.
The webhook response format is a valid Teams bot framework response with
an Adaptive Card attachment.
"""
    )

st.divider()

# Teams message simulator
st.subheader("Send a Teams Message")

if "teams_history" not in st.session_state:
    st.session_state.teams_history = []

with st.form("teams_form"):
    sender_name = st.text_input("Sender name", value="Warehouse Operator")
    message_text = st.text_area(
        "Message",
        placeholder="How do I troubleshoot a bin stuck error?",
        height=100,
    )
    send_button = st.form_submit_button("Send via Webhook", type="primary")

if send_button and message_text:
    # Build Teams activity payload
    activity = {
        "type": "message",
        "text": message_text,
        "from": {"id": "preview-user", "name": sender_name},
        "channelId": "streamlit-preview",
    }

    with st.spinner("Processing through RAG pipeline..."):
        try:
            resp = api_post("/teams/webhook", json=activity)
            if resp.status_code == 200:
                response_data = resp.json()
                st.session_state.teams_history.append(
                    {
                        "sender": sender_name,
                        "message": message_text,
                        "response": response_data,
                    }
                )
            else:
                st.error(f"Webhook returned {resp.status_code}: {resp.text}")
        except Exception as e:
            st.error(f"Error calling webhook: {e}")

elif send_button:
    st.warning("Please enter a message.")

# Display conversation history
if st.session_state.teams_history:
    st.divider()
    st.subheader("Conversation")

    for entry in reversed(st.session_state.teams_history):
        # User message (Teams style)
        with st.container(border=True):
            st.markdown(f"**{entry['sender']}** (Teams)")
            st.markdown(entry["message"])

        # Bot response (Adaptive Card preview)
        response = entry.get("response", {})
        attachments = response.get("attachments", [])

        with st.container(border=True):
            st.markdown("**Warehouse AI Bot**")
            for attachment in attachments:
                card = attachment.get("content", {})
                body = card.get("body", [])
                for block in body:
                    block_type = block.get("type", "")
                    if block_type == "TextBlock":
                        text = block.get("text", "")
                        weight = block.get("weight", "")
                        if weight == "Bolder":
                            st.markdown(f"**{text}**")
                        elif block.get("color") == "Attention":
                            st.error(text)
                        else:
                            st.markdown(text)
                    elif block_type == "FactSet":
                        for fact in block.get("facts", []):
                            st.caption(f"**{fact['title']}:** {fact['value']}")

        st.markdown("---")

    # Raw JSON viewer
    with st.expander("View raw webhook response (JSON)"):
        if st.session_state.teams_history:
            latest = st.session_state.teams_history[-1]["response"]
            st.json(latest)
