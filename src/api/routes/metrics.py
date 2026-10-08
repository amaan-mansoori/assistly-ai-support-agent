"""Admin-only process-local operational metrics."""
from fastapi import APIRouter, Depends, Request

from src.api.security import Principal, require_roles

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


@router.get("", summary="Read process-local agent counters and latency summaries")
def get_metrics(
    request: Request,
    _principal: Principal = Depends(require_roles("admin")),
):
    del _principal
    return request.app.state.metrics.snapshot()
