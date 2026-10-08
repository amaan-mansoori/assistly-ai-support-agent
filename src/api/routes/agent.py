"""Explicit runtime-agent endpoint reusing the conversation application workflow."""
from fastapi import APIRouter, Depends, Header, Request, Response
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.errors import PlatformError
from src.api.routes.conversations import submit_agent_request
from src.api.schemas import AgentRespondRequest, MessageSubmission
from src.api.security import Principal, require_roles

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


@router.post("/respond", response_model=MessageSubmission)
def respond(
    payload: AgentRespondRequest,
    request: Request,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    session: Session = Depends(get_db),
    principal: Principal = Depends(require_roles("customer")),
):
    if not idempotency_key:
        raise PlatformError(
            400, "IDEMPOTENCY_KEY_REQUIRED", "Provide an Idempotency-Key header."
        )
    return submit_agent_request(
        payload.conversation_id,
        payload.message,
        idempotency_key,
        request,
        response,
        session,
        principal,
    )
