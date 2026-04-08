"""Microsoft Teams adaptive card builder for bot responses."""

from __future__ import annotations

from typing import Any

from warehouse_ai.agent.state import SourceChunk


def build_answer_card(answer: str, sources: list[SourceChunk]) -> dict[str, Any]:
    """Build a Teams adaptive card containing the answer and source citations."""
    body: list[dict[str, Any]] = [
        {
            "type": "TextBlock",
            "text": "Warehouse Knowledge Assistant",
            "weight": "Bolder",
            "size": "Medium",
        },
        {
            "type": "TextBlock",
            "text": answer,
            "wrap": True,
        },
    ]

    if sources:
        source_lines = []
        seen = set()
        for s in sources:
            key = s.document_title
            if key not in seen:
                source_lines.append(
                    f"- {s.document_title} (relevance: {s.relevance_score:.0%})"
                )
                seen.add(key)
        body.append(
            {
                "type": "FactSet",
                "facts": [
                    {"title": "Sources", "value": "\n".join(source_lines)},
                ],
            }
        )

    card = {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.4",
        "body": body,
    }

    return card


def build_teams_response(answer: str, sources: list[SourceChunk]) -> dict[str, Any]:
    """Build a complete Teams bot framework response message."""
    card = build_answer_card(answer, sources)
    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card,
            }
        ],
    }


def build_error_card(error_message: str) -> dict[str, Any]:
    """Build a Teams adaptive card for error responses."""
    card = {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "Warehouse Knowledge Assistant",
                "weight": "Bolder",
                "size": "Medium",
            },
            {
                "type": "TextBlock",
                "text": f"Sorry, I encountered an error: {error_message}",
                "wrap": True,
                "color": "Attention",
            },
        ],
    }
    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card,
            }
        ],
    }
