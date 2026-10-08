"""Persistent human-review queue and authorization policy."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.errors import PlatformError
from src.api.security import Principal
from src.db.models import Conversation, HumanReviewTicket, User


class TicketService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(
        self,
        principal: Principal,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[HumanReviewTicket]:
        statement = select(HumanReviewTicket)
        if principal.role == "agent":
            statement = statement.where(
                (HumanReviewTicket.assigned_to == principal.id)
                | (
                    (HumanReviewTicket.status == "open")
                    & HumanReviewTicket.assigned_to.is_(None)
                )
            )
        elif principal.role != "admin":
            raise PlatformError(403, "FORBIDDEN", "Only support staff can view the ticket queue.")
        if status is not None:
            if status not in {"open", "assigned", "in_progress", "resolved", "closed"}:
                raise PlatformError(422, "INVALID_TICKET_STATUS", "Ticket status is invalid.")
            statement = statement.where(HumanReviewTicket.status == status)
        return list(
            self.session.scalars(
                statement.order_by(
                    HumanReviewTicket.created_at.asc(), HumanReviewTicket.id
                ).offset(offset).limit(limit)
            )
        )

    def get(self, ticket_id: str, principal: Principal) -> HumanReviewTicket:
        ticket = self.session.get(HumanReviewTicket, ticket_id)
        if ticket is None:
            raise PlatformError(404, "TICKET_NOT_FOUND", "Ticket was not found.")
        if principal.role == "admin":
            return ticket
        if principal.role == "agent" and (
            ticket.assigned_to == principal.id
            or (ticket.status == "open" and ticket.assigned_to is None)
        ):
            return ticket
        raise PlatformError(404, "TICKET_NOT_FOUND", "Ticket was not found.")

    def assign(
        self, ticket_id: str, principal: Principal, assigned_to: str | None
    ) -> HumanReviewTicket:
        ticket = self.get(ticket_id, principal)
        if principal.role == "agent":
            if assigned_to not in (None, principal.id):
                raise PlatformError(403, "FORBIDDEN", "Agents may only assign tickets to themselves.")
            assigned_to = principal.id
        elif principal.role != "admin":
            raise PlatformError(403, "FORBIDDEN", "Only support staff can assign tickets.")
        if assigned_to is not None:
            user = self.session.get(User, assigned_to)
            if user is None or user.role != "agent":
                raise PlatformError(422, "INVALID_ASSIGNEE", "Tickets may only be assigned to an agent.")
        if ticket.status in {"resolved", "closed"}:
            raise PlatformError(409, "TICKET_CLOSED", "A resolved or closed ticket cannot be assigned.")
        ticket.assigned_to = assigned_to
        ticket.status = "assigned" if assigned_to else "open"
        self.session.commit()
        self.session.refresh(ticket)
        return ticket

    def start(self, ticket_id: str, principal: Principal) -> HumanReviewTicket:
        ticket = self.get(ticket_id, principal)
        if principal.role != "admin" and ticket.assigned_to != principal.id:
            raise PlatformError(403, "FORBIDDEN", "Assign the ticket to yourself before starting work.")
        if ticket.status not in {"assigned", "in_progress"}:
            raise PlatformError(409, "INVALID_TICKET_TRANSITION", "Only assigned tickets can be started.")
        ticket.status = "in_progress"
        self.session.commit()
        self.session.refresh(ticket)
        return ticket

    def resolve(
        self,
        ticket_id: str,
        principal: Principal,
        resolution: dict[str, Any],
    ) -> HumanReviewTicket:
        ticket = self.get(ticket_id, principal)
        if principal.role != "admin" and ticket.assigned_to != principal.id:
            raise PlatformError(403, "FORBIDDEN", "Only the assigned agent may resolve this ticket.")
        if ticket.status in {"resolved", "closed"}:
            raise PlatformError(409, "TICKET_CLOSED", "This ticket is already resolved or closed.")
        ticket.status = "resolved"
        ticket.resolution_metadata = resolution
        conversation = self.session.get(Conversation, ticket.conversation_id)
        if conversation is not None:
            conversation.status = "resolved"
        self.session.commit()
        self.session.refresh(ticket)
        return ticket
