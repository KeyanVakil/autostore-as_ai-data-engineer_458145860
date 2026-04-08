"""Microsoft Teams webhook endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage

from warehouse_ai.api.dependencies import get_agent
from warehouse_ai.api.models import TeamsActivity
from warehouse_ai.teams.cards import build_error_card, build_teams_response

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/teams/webhook")
async def teams_webhook(
    activity: TeamsActivity,
    agent=Depends(get_agent),
):
    """Handle incoming Microsoft Teams bot messages."""
    if activity.type != "message":
        raise HTTPException(status_code=400, detail=f"Unsupported activity type: {activity.type}")

    if not activity.text.strip():
        raise HTTPException(status_code=400, detail="Message text is empty")

    try:
        result = agent.invoke(
            {
                "messages": [HumanMessage(content=activity.text)],
                "query": activity.text,
                "session_id": f"teams-{activity.from_.get('id', 'unknown')}",
            }
        )

        answer = result.get("answer", "")
        sources = result.get("sources", [])
        return build_teams_response(answer, sources)

    except Exception as e:
        logger.error("Teams webhook error: %s", e)
        return build_error_card(str(e))
