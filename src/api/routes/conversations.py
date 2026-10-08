"""Conversation and message endpoints backed by application services."""
from fastapi import APIRouter, Depends, Header, Request, Response, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.errors import PlatformError
from src.api.schemas import (
    AgentRunOut,
    ConversationCreate,
    ConversationOut,
    MessageCreate,
    MessageOut,
    MessageSubmission,
)
from src.api.security import Principal, get_current_user, require_roles
from src.application.conversation_service import ConversationService
from src.application.support_service import SupportService
from src.db.models import Conversation, Message

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


def _conversation_out(conversation: Conversation) -> ConversationOut:
    return ConversationOut(
        id=conversation.id,
        status=conversation.status,
        metadata=conversation.metadata_json,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def _message_out(message: Message) -> MessageOut:
    return MessageOut(
        id=message.id,
        conversation_id=message.conversation_id,
        sender_type=message.sender_type,
        content=message.content,
        created_at=message.created_at,
        metadata=message.metadata_json,
    )


def _run_out(run) -> AgentRunOut:
    return AgentRunOut(
        id=run.id,
        conversation_id=run.conversation_id,
        request_id=run.request_id,
        intent=run.intent,
        intent_confidence=run.intent_confidence,
        intent_reason=run.intent_reason,
        intent_source=run.intent_source,
        evidence_status=run.evidence_status,
        evidence_reason=run.evidence_reason,
        evidence=run.evidence_summary,
        grounding=run.grounding_result,
        decision=run.decision,
        escalation_reason=run.escalation_reason,
        provider=run.provider,
        model=run.model,
        latency_ms=run.latency_ms,
        processing_metadata=run.processing_metadata,
        error_category=run.error_category,
    )


def _enforce_message_limit(request: Request, principal: Principal) -> None:
    if not request.app.state.rate_limiter.allow(f"messages:{principal.id}"):
        raise PlatformError(
            429,
            "RATE_LIMIT_EXCEEDED",
            "Message request limit exceeded; retry after the current minute.",
        )


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    session: Session = Depends(get_db),
    principal: Principal = Depends(require_roles("customer")),
):
    conversation = ConversationService(session).create(principal.id, payload.metadata)
    return _conversation_out(conversation)


@router.get("", response_model=list[ConversationOut])
def list_conversations(
    limit: int = 50,
    offset: int = 0,
    session: Session = Depends(get_db),
    principal: Principal = Depends(get_current_user),
):
    if not 1 <= limit <= 100 or offset < 0:
        raise PlatformError(422, "INVALID_PAGINATION", "Pagination parameters are out of range.")
    service = ConversationService(session)
    return [_conversation_out(item) for item in service.list_for(principal, limit, offset)]


@router.get("/{conversation_id}", response_model=ConversationOut)
def get_conversation(
    conversation_id: str,
    session: Session = Depends(get_db),
    principal: Principal = Depends(get_current_user),
):
    conversation = ConversationService(session).get(conversation_id, principal)
    return _conversation_out(conversation)


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
def list_messages(
    conversation_id: str,
    session: Session = Depends(get_db),
    principal: Principal = Depends(get_current_user),
):
    service = ConversationService(session)
    conversation = service.get(conversation_id, principal)
    return [_message_out(item) for item in service.messages_for(conversation)]


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageSubmission,
    status_code=status.HTTP_200_OK,
)
def create_message(
    conversation_id: str,
    payload: MessageCreate,
    request: Request,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    session: Session = Depends(get_db),
    principal: Principal = Depends(require_roles("customer")),
):
    _enforce_message_limit(request, principal)
    if not idempotency_key or len(idempotency_key) > 128:
        raise PlatformError(
            400, "IDEMPOTENCY_KEY_REQUIRED", "Provide an Idempotency-Key header of at most 128 characters."
        )
    if any(not (char.isalnum() or char in "-_.:") for char in idempotency_key):
        raise PlatformError(400, "INVALID_IDEMPOTENCY_KEY", "The idempotency key contains unsupported characters.")
    conversations = ConversationService(session)
    conversation = conversations.get(conversation_id, principal)
    customer_message, duplicate = conversations.add_customer_message(
        conversation, payload.content, idempotency_key
    )
    if duplicate:
        existing_run = customer_message.agent_run
        if existing_run is None:
            response.status_code = status.HTTP_202_ACCEPTED
            return MessageSubmission(
                status="processing", customer_message=_message_out(customer_message)
            )
    settings = request.app.state.settings
    run, assistant_message, ticket = SupportService(
        session,
        request.app.state.agent_factory,
        request.app.state.provider_name,
        request.app.state.model_name,
        request.app.state.metrics,
        settings.conversation_history_window,
        settings.conversation_history_max_chars,
    ).process_customer_message(
        conversation,
        customer_message,
        request.state.request_id,
    )
    return MessageSubmission(
        status=run.decision,
        customer_message=_message_out(customer_message),
        assistant_message=_message_out(assistant_message) if assistant_message else None,
        agent_run=_run_out(run),
        ticket_id=ticket.id if ticket else None,
    )


def submit_agent_request(
    conversation_id: str,
    content: str,
    idempotency_key: str,
    request: Request,
    response: Response,
    session: Session,
    principal: Principal,
) -> MessageSubmission:
    return create_message(
        conversation_id,
        MessageCreate(content=content),
        request,
        response,
        idempotency_key,
        session,
        principal,
    )
