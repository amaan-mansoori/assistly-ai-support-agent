"""Typed contracts for the support-agent core."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, Sequence
from uuid import uuid4

DecisionKind = Literal["auto_handle", "escalate"]
EvidenceStatus = Literal["none", "weak", "sufficient"]


@dataclass(frozen=True)
class AgentRequest:
    message: str
    conversation_history: Sequence[str] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)
    requested_intent: str | None = None
    request_id: str = field(default_factory=lambda: str(uuid4()))

    @classmethod
    def from_value(cls, value: AgentRequest | Mapping[str, Any]) -> AgentRequest:
        if isinstance(value, cls):
            request = value
        elif isinstance(value, Mapping):
            message = value.get("message", value.get("customer_message"))
            history = value.get("conversation_history", ())
            metadata = value.get("metadata", {})
            requested_intent = value.get("requested_intent")
            request_id = value.get("request_id") or str(uuid4())
            if not isinstance(message, str):
                raise ValueError("message must be a string")
            if not isinstance(history, (list, tuple)) or any(
                not isinstance(turn, str) for turn in history
            ):
                raise ValueError("conversation_history must be a list of strings")
            if not isinstance(metadata, Mapping) or any(
                not isinstance(key, str) or not isinstance(item, str)
                for key, item in metadata.items()
            ):
                raise ValueError("metadata must be a mapping of strings")
            if requested_intent is not None and not isinstance(requested_intent, str):
                raise ValueError("requested_intent must be a string")
            if not isinstance(request_id, str):
                raise ValueError("request_id must be a string")
            request = cls(
                message=message,
                conversation_history=tuple(history),
                metadata=dict(metadata),
                requested_intent=requested_intent,
                request_id=request_id,
            )
        else:
            raise ValueError("request must be an AgentRequest or mapping")

        if not isinstance(request.message, str):
            raise ValueError("message must be a string")
        if not isinstance(request.request_id, str):
            raise ValueError("request_id must be a string")
        if not isinstance(request.conversation_history, (list, tuple)) or any(
            not isinstance(turn, str) for turn in request.conversation_history
        ):
            raise ValueError("conversation_history must be a list of strings")
        if not isinstance(request.metadata, Mapping) or any(
            not isinstance(key, str) or not isinstance(item, str)
            for key, item in request.metadata.items()
        ):
            raise ValueError("metadata must be a mapping of strings")
        if not request.request_id:
            raise ValueError("request_id must not be empty")
        if len(request.request_id) > 128 or any(
            not (char.isalnum() or char in "-_.:") for char in request.request_id
        ):
            raise ValueError("request_id contains unsupported characters")
        if request.requested_intent is not None and not isinstance(
            request.requested_intent, str
        ):
            raise ValueError("requested_intent must be a string")
        return request


@dataclass(frozen=True)
class AgentIntent:
    name: str
    confidence: float | None
    reason: str
    source: str


@dataclass(frozen=True)
class AgentEvidence:
    customer_message: str
    support_response: str
    source_id: str
    retrieval_score: float
    provenance: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class GroundingResult:
    supported: bool
    score: float | None
    evidence_token_support_rate: float
    unsupported_claims: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class AgentDecision:
    decision: DecisionKind
    reason: str


@dataclass(frozen=True)
class AgentResponse:
    request_id: str
    intent: str | None
    intent_confidence: float | None
    intent_reason: str | None
    intent_source: str | None
    evidence: tuple[AgentEvidence, ...]
    evidence_status: EvidenceStatus
    evidence_reason: str
    draft_reply: str | None
    model_grounding_confidence: float | None
    needs_human_review: bool
    grounding: GroundingResult | None
    decision: AgentDecision
    processing_metadata: Mapping[str, Any] = field(default_factory=dict)
    error: str | None = None
