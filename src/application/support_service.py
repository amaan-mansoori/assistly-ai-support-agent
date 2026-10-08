"""Application service integrating persisted conversations with the Phase 1 agent."""
from __future__ import annotations

import logging
import time
from dataclasses import asdict
from typing import Any, Callable, Mapping, Protocol

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.agent.context import bounded_conversation_history
from src.agent.models import AgentDecision, AgentRequest, AgentResponse
from src.db.models import AgentRun, Conversation, HumanReviewTicket, Message
from src.platform.metrics import MetricsRegistry

logger = logging.getLogger(__name__)


class Agent(Protocol):
    def handle(self, value: AgentRequest | Mapping[str, Any]) -> AgentResponse:
        ...


class SupportService:
    def __init__(
        self,
        session: Session,
        agent_factory: Callable[[], Agent],
        provider: str,
        model: str,
        metrics: MetricsRegistry | None = None,
        history_window: int = 12,
        history_max_chars: int = 12_000,
    ) -> None:
        if history_window < 1 or history_max_chars < 1:
            raise ValueError("conversation history limits must be positive")
        self.session = session
        self.agent_factory = agent_factory
        self.provider = provider
        self.model = model
        self.metrics = metrics
        self.history_window = history_window
        self.history_max_chars = history_max_chars

    def process_customer_message(
        self,
        conversation: Conversation,
        customer_message: Message,
        request_id: str,
    ) -> tuple[AgentRun, Message | None, HumanReviewTicket | None]:
        existing_run = self.session.scalar(
            select(AgentRun).where(AgentRun.message_id == customer_message.id)
        )
        if existing_run is not None:
            return self._existing_result(existing_run)

        prior_messages = list(
            self.session.scalars(
                select(Message)
                .where(
                    Message.conversation_id == conversation.id,
                    Message.id != customer_message.id,
                )
                .order_by(desc(Message.created_at), desc(Message.id))
                .limit(self.history_window)
            )
        )
        history = bounded_conversation_history(
            tuple(
                item.content
                for item in reversed(prior_messages)
                if item.sender_type in {"customer", "assistant"}
            ),
            max_turns=self.history_window,
            max_chars=self.history_max_chars,
        )
        started = time.perf_counter()
        try:
            agent = self.agent_factory()
            result: AgentResponse = agent.handle(
                {
                    "message": customer_message.content,
                    "conversation_history": history,
                    "request_id": request_id,
                }
            )
        except Exception as exc:
            logger.error(
                "agent_service_failure",
                extra={"request_id": request_id, "error_type": type(exc).__name__},
            )
            result = self._safe_failure(request_id)
        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        if self.metrics is not None:
            self.metrics.record_agent_result(result, latency_ms)
        grounding = asdict(result.grounding) if result.grounding is not None else None
        evidence = [
            {
                "source_id": item.source_id,
                "retrieval_score": item.retrieval_score,
                "customer_message": item.customer_message,
                "support_response": item.support_response,
            }
            for item in result.evidence
        ]
        stage_timings = result.processing_metadata.get("stage_timings_ms", {})
        provider_was_called = (
            isinstance(stage_timings, Mapping)
            and "generation_latency_ms" in stage_timings
        )
        run = AgentRun(
            conversation_id=conversation.id,
            message_id=customer_message.id,
            request_id=request_id,
            intent=result.intent,
            intent_confidence=result.intent_confidence,
            intent_reason=result.intent_reason,
            intent_source=result.intent_source,
            evidence_status=result.evidence_status,
            evidence_reason=result.evidence_reason,
            draft_reply=result.draft_reply,
            evidence_summary=evidence,
            grounding_result=grounding,
            decision=result.decision.decision,
            escalation_reason=(
                result.decision.reason
                if result.decision.decision == "escalate"
                else None
            ),
            provider=self.provider if provider_was_called else None,
            model=self.model if provider_was_called else None,
            latency_ms=latency_ms,
            processing_metadata=dict(result.processing_metadata),
            error_category=result.error,
        )
        self.session.add(run)
        self.session.flush()
        logger.info(
            "agent_run_persisted",
            extra={
                "request_id": request_id,
                "conversation_id": conversation.id,
                "agent_run_id": run.id,
                "intent": run.intent,
                "intent_confidence": run.intent_confidence,
                "evidence_status": run.evidence_status,
                "decision": run.decision,
                "provider": run.provider,
                "model": run.model,
                "latency_ms": run.latency_ms,
                "error_category": run.error_category,
            },
        )
        ticket = None
        assistant_message = None
        if result.decision.decision == "escalate":
            ticket = HumanReviewTicket(
                conversation_id=conversation.id,
                agent_run_id=run.id,
                status="open",
                priority=self._priority(result.intent),
                reason=result.decision.reason,
            )
            conversation.status = "waiting_for_agent"
            self.session.add(ticket)
        elif result.draft_reply:
            assistant_message = Message(
                conversation_id=conversation.id,
                sender_type="assistant",
                content=result.draft_reply,
                metadata_json={"agent_run_id": run.id, "delivery_status": "auto_handled"},
            )
            conversation.status = "open"
            self.session.add(assistant_message)
        self.session.commit()
        self.session.refresh(run)
        if assistant_message is not None:
            self.session.refresh(assistant_message)
        if ticket is not None:
            self.session.refresh(ticket)
        return run, assistant_message, ticket

    def _existing_result(
        self, run: AgentRun
    ) -> tuple[AgentRun, Message | None, HumanReviewTicket | None]:
        assistant = self.session.scalar(
            select(Message).where(
                Message.conversation_id == run.conversation_id,
                Message.metadata_json["agent_run_id"].as_string() == run.id,
            )
        )
        ticket = self.session.scalar(
            select(HumanReviewTicket).where(HumanReviewTicket.agent_run_id == run.id)
        )
        return run, assistant, ticket

    @staticmethod
    def _priority(intent: str | None) -> str:
        if intent == "account_access_security":
            return "urgent"
        if intent in {"payment_charge_issue", "delivery_marked_delivered_missing"}:
            return "high"
        return "normal"

    @staticmethod
    def _safe_failure(request_id: str) -> AgentResponse:
        return AgentResponse(
            request_id=request_id,
            intent=None,
            intent_confidence=None,
            intent_reason=None,
            intent_source=None,
            evidence=(),
            evidence_status="none",
            evidence_reason="The agent service could not safely process this request.",
            draft_reply=None,
            model_grounding_confidence=None,
            needs_human_review=True,
            grounding=None,
            decision=AgentDecision(
                "escalate", "The agent service failed; human review is required."
            ),
            error="agent_service_failed",
        )
