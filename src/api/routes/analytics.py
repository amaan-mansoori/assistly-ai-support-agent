"""Administrator-only database analytics."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.schemas import AnalyticsOut
from src.api.security import Principal, require_roles
from src.application.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("", response_model=AnalyticsOut)
def get_analytics(
    session: Session = Depends(get_db),
    _principal: Principal = Depends(require_roles("admin")),
):
    return AnalyticsService(session).summary()
