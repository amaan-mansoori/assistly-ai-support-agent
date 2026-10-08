"""Conversation and message persistence with ownership and idempotency rules."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.api.errors import PlatformError
from src.api.security import Principal
from src.db.models import Conversation, HumanReviewTicket, Message


class ConversationService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, owner_id: str, metadata: dict[str, Any]) -> Conversation:
        conversation = Conversation(user_id=owner_id, metadata_json=metadata)
        self.session.add(conversation)
        self.session.commit()
        self.session.refresh(conversation)
        return conversation

    def get(self, conversation_id: str, principal: Principal) -> Conversation:
        conversation = self.session.get(Conversation, conversation_id)
        if conversation is None:
            raise PlatformError(404, "CONVERSATION_NOT_FOUND", "Conversation was not found.")
        if principal.role == "customer":
            if conversation.user_id != principal.id:
                raise PlatformError(404, "CONVERSATION_NOT_FOUND", "Conversation was not found.")
        elif principal.role == "agent":
            self._require_queue_access(conversation.id, principal.id)
        elif principal.role != "admin":
            raise PlatformError(403, "FORBIDDEN", "You do not have permission to view this conversation.")
        return conversation

    def list_for(self, principal: Principal, limit: int, offset: int) -> list[Conversation]:
        statement = select(Conversation)
        if principal.role == "customer":
            statement = statement.where(Conversation.user_id == principal.id)
        elif principal.role == "agent":
            visible_conversations = select(HumanReviewTicket.conversation_id).where(
                (HumanReviewTicket.assigned_to == principal.id)
                | (
                    (HumanReviewTicket.status == "open")
                    & HumanReviewTicket.assigned_to.is_(None)
                )
            )
            statement = statement.where(Conversation.id.in_(visible_conversations))
        elif principal.role != "admin":
            raise PlatformError(403, "FORBIDDEN", "You do not have permission to list conversations.")
        return list(
            self.session.scalars(
                statement.order_by(Conversation.updated_at.desc()).offset(offset).limit(limit)
            )
        )

    def messages_for(self, conversation: Conversation) -> list[Message]:
        return list(
            self.session.scalars(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.created_at, Message.id)
            )
        )

    def add_customer_message(
        self,
        conversation: Conversation,
        content: str,
        idempotency_key: str,
    ) -> tuple[Message, bool]:
        existing = self.session.scalar(
            select(Message).where(
                Message.conversation_id == conversation.id,
                Message.idempotency_key == idempotency_key,
            )
        )
        if existing is not None:
            self._ensure_same_content(existing, content)
            return existing, True
        message = Message(
            conversation_id=conversation.id,
            sender_type="customer",
            content=content,
            idempotency_key=idempotency_key,
        )
        conversation.status = "open"
        self.session.add(message)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            existing = self.session.scalar(
                select(Message).where(
                    Message.conversation_id == conversation.id,
                    Message.idempotency_key == idempotency_key,
                )
            )
            if existing is None:
                raise
            self._ensure_same_content(existing, content)
            return existing, True
        self.session.refresh(message)
        return message, False

    @staticmethod
    def _ensure_same_content(message: Message, content: str) -> None:
        if message.content != content:
            raise PlatformError(
                409,
                "IDEMPOTENCY_KEY_REUSED",
                "The idempotency key was already used for a different message.",
            )

    def _require_queue_access(self, conversation_id: str, agent_id: str) -> None:
        allowed = self.session.scalar(
            select(HumanReviewTicket.id).where(
                HumanReviewTicket.conversation_id == conversation_id,
                (HumanReviewTicket.assigned_to == agent_id)
                | (
                    (HumanReviewTicket.status == "open")
                    & HumanReviewTicket.assigned_to.is_(None)
                ),
            )
        )
        if allowed is None:
            raise PlatformError(404, "CONVERSATION_NOT_FOUND", "Conversation was not found.")
