"""Validated request/response contracts for the REST API."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=256)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if value.count("@") != 1 or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("email must be a valid address")
        return value


class UserLogin(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=256)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str | None
    role: str
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class ConversationCreate(BaseModel):
    metadata: dict[str, Any] = Field(default_factory=dict, max_length=64)


class ConversationOut(BaseModel):
    id: str
    status: str
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=10000)

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("content must not be blank")
        return value.strip()


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    sender_type: str
    content: str
    created_at: datetime
    metadata: dict[str, Any]


class AgentRunOut(BaseModel):
    id: str
    conversation_id: str
    request_id: str
    intent: str | None
    intent_confidence: float | None
    intent_reason: str | None
    intent_source: str | None
    evidence_status: str
    evidence_reason: str | None
    evidence: list[dict[str, Any]]
    grounding: dict[str, Any] | None
    decision: str
    escalation_reason: str | None
    provider: str | None
    model: str | None
    latency_ms: float
    processing_metadata: dict[str, Any]
    error_category: str | None


class TicketAgentRunOut(AgentRunOut):
    draft_reply: str | None


class MessageSubmission(BaseModel):
    status: str
    customer_message: MessageOut
    assistant_message: MessageOut | None = None
    agent_run: AgentRunOut | None = None
    ticket_id: str | None = None


class AgentRespondRequest(BaseModel):
    conversation_id: str = Field(min_length=1, max_length=36)
    message: str = Field(
        min_length=1,
        max_length=10000,
        validation_alias=AliasChoices("message", "content"),
    )

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be blank")
        return value.strip()


class TicketOut(BaseModel):
    id: str
    conversation_id: str
    agent_run_id: str | None
    status: str
    priority: str
    reason: str
    assigned_to: str | None
    resolution_metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class TicketDetail(TicketOut):
    conversation: ConversationOut
    messages: list[MessageOut]
    agent_run: TicketAgentRunOut | None


class TicketAssign(BaseModel):
    assigned_to: str | None = Field(default=None, min_length=1, max_length=36)


class TicketResolve(BaseModel):
    resolution_metadata: dict[str, Any] = Field(default_factory=dict, max_length=64)


class FeedbackCreate(BaseModel):
    conversation_id: str | None = Field(default=None, min_length=1, max_length=36)
    agent_run_id: str | None = Field(default=None, min_length=1, max_length=36)
    rating: int = Field(ge=1, le=5)
    category: str | None = Field(default=None, max_length=64)
    comment: str | None = Field(default=None, max_length=4000)

    @field_validator("comment")
    @classmethod
    def strip_comment(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()
        return value or None


class FeedbackOut(BaseModel):
    id: str
    conversation_id: str | None
    agent_run_id: str | None
    rating: int
    category: str | None
    comment: str | None
    created_at: datetime


class AnalyticsOut(BaseModel):
    total_conversations: int
    auto_handle_rate: float | None
    escalation_rate: float | None
    resolution_rate: float | None
    average_latency_ms: float | None
    average_feedback_rating: float | None
    intent_distribution: dict[str, int]
    error_categories: dict[str, int]
