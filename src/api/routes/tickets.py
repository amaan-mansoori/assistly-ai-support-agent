"""Human-review ticket queue endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.errors import PlatformError
from src.api.routes.conversations import _conversation_out, _message_out, _run_out
from src.api.schemas import (
    ConversationOut,
    MessageOut,
    TicketAssign,
    TicketAgentRunOut,
    TicketDetail,
    TicketOut,
    TicketResolve,
)
from src.api.security import Principal, require_roles
from src.application.conversation_service import ConversationService
from src.application.ticket_service import TicketService
from src.db.models import AgentRun, HumanReviewTicket

router = APIRouter(prefix="/api/v1/tickets", tags=["human review"])


def _ticket_out(ticket: HumanReviewTicket) -> TicketOut:
    return TicketOut(
        id=ticket.id,
        conversation_id=ticket.conversation_id,
        agent_run_id=ticket.agent_run_id,
        status=ticket.status,
        priority=ticket.priority,
        reason=ticket.reason,
        assigned_to=ticket.assigned_to,
        resolution_metadata=ticket.resolution_metadata,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


def _ticket_run_out(run) -> TicketAgentRunOut:
    return TicketAgentRunOut(
        **_run_out(run).model_dump(),
        draft_reply=run.draft_reply,
    )


@router.get("", response_model=list[TicketOut])
def list_tickets(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    session: Session = Depends(get_db),
    principal: Principal = Depends(require_roles("agent", "admin")),
):
    if not 1 <= limit <= 100 or offset < 0:
        raise PlatformError(422, "INVALID_PAGINATION", "Pagination parameters are out of range.")
    rows = TicketService(session).list(principal, status, limit, offset)
    return [_ticket_out(ticket) for ticket in rows]


@router.get("/{ticket_id}", response_model=TicketDetail)
def get_ticket(
    ticket_id: str,
    session: Session = Depends(get_db),
    principal: Principal = Depends(require_roles("agent", "admin")),
):
    ticket = TicketService(session).get(ticket_id, principal)
    conversation = ticket.conversation
    conversation_out: ConversationOut = _conversation_out(conversation)
    messages: list[MessageOut] = [
        _message_out(item) for item in ConversationService(session).messages_for(conversation)
    ]
    run = (
        session.get(AgentRun, ticket.agent_run_id)
        if ticket.agent_run_id is not None
        else None
    )
    return TicketDetail(
        **_ticket_out(ticket).model_dump(),
        conversation=conversation_out,
        messages=messages,
        agent_run=_ticket_run_out(run) if run else None,
    )


@router.post("/{ticket_id}/assign", response_model=TicketOut)
def assign_ticket(
    ticket_id: str,
    payload: TicketAssign,
    session: Session = Depends(get_db),
    principal: Principal = Depends(require_roles("agent", "admin")),
):
    ticket = TicketService(session).assign(ticket_id, principal, payload.assigned_to)
    return _ticket_out(ticket)


@router.post("/{ticket_id}/start", response_model=TicketOut)
def start_ticket(
    ticket_id: str,
    session: Session = Depends(get_db),
    principal: Principal = Depends(require_roles("agent", "admin")),
):
    return _ticket_out(TicketService(session).start(ticket_id, principal))


@router.post("/{ticket_id}/resolve", response_model=TicketOut)
def resolve_ticket(
    ticket_id: str,
    payload: TicketResolve,
    session: Session = Depends(get_db),
    principal: Principal = Depends(require_roles("agent", "admin")),
):
    ticket = TicketService(session).resolve(
        ticket_id, principal, payload.resolution_metadata
    )
    return _ticket_out(ticket)
