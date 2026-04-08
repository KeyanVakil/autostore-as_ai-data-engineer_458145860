"""Pipeline monitoring endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from warehouse_ai.api.dependencies import get_delta
from warehouse_ai.api.models import PipelineRunStatus, PipelineRunsResponse
from warehouse_ai.storage.delta import DeltaStore

router = APIRouter()


@router.get("/pipeline/runs", response_model=PipelineRunsResponse)
async def get_pipeline_runs(delta: DeltaStore = Depends(get_delta)):
    """Get pipeline run history."""
    runs = delta.get_pipeline_runs()
    return PipelineRunsResponse(
        runs=[PipelineRunStatus(**r) for r in runs],
    )
