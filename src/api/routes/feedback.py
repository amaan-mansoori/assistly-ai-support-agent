"""Customer feedback endpoint."""
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.schemas import FeedbackCreate, FeedbackOut
from src.api.security import Principal, require_roles
from src.application.feedback_service import FeedbackService

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    payload: FeedbackCreate,
    request: Request,
    session: Session = Depends(get_db),
    principal: Principal = Depends(require_roles("customer")),
):
    row = FeedbackService(session).create(
        principal,
        conversation_id=payload.conversation_id,
        agent_run_id=payload.agent_run_id,
        rating=payload.rating,
        category=payload.category,
        comment=payload.comment,
    )
    request.app.state.metrics.record_feedback(row.rating)
    return FeedbackOut(
        id=row.id,
        conversation_id=row.conversation_id,
        agent_run_id=row.agent_run_id,
        rating=row.rating,
        category=row.category,
        comment=row.comment,
        created_at=row.created_at,
    )
