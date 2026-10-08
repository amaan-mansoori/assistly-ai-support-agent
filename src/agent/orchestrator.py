"""End-to-end support-agent orchestration around the existing core components."""
from __future__ import annotations

import logging
import time
import unicodedata
from dataclasses import replace
from typing import Any, Callable, Mapping
from uuid import uuid4

from src.agent.config import AgentConfig
from src.agent.context import bounded_conversation_history
from src.agent.escalation import SENSITIVE_INTENTS, decide_escalation
from src.agent.evidence import EvidenceAssessment, assess_evidence, convert_evidence
from src.agent.grounding import validate_grounding
from src.agent.intent import INTENT_NAMES, IntentDetector
from src.agent.models import (
    AgentDecision,
    AgentEvidence,
    AgentIntent,
    AgentRequest,
    AgentResponse,
    EvidenceStatus,
    GroundingResult,
)
from src.agent.reply_generator import (
    ReplyGenerationError,
    configured_llm_call,
    generate_reply,
)
from src.retrieval.historical_retriever import HistoricalRetriever
from src.retrieval.interfaces import Retriever

logger = logging.getLogger(__name__)


class SupportAgent:
    """Coordinate intent detection, evidence retrieval, drafting, and policy."""

    def __init__(
        self,
        retriever: Retriever,
        llm_call: Callable[[str, str], str],
        config: AgentConfig | None = None,
        intent_detector: IntentDetector | None = None,
    ) -> None:
        self.retriever = retriever
        self.llm_call = llm_call
        self.config = config or AgentConfig.load()
        self.intent_detector = intent_detector or IntentDetector()

    @classmethod
    def from_repository(cls, config: AgentConfig | None = None) -> SupportAgent:
        config = config or AgentConfig.load()
        retriever, _ = HistoricalRetriever.build()
        llm_call = configured_llm_call(
            config.provider,
            config.model,
            timeout_seconds=config.provider_timeout_seconds,
            max_retries=config.provider_max_retries,
        )
        return cls(retriever, llm_call, config)

    def handle(self, value: AgentRequest | Mapping[str, Any]) -> AgentResponse:
        started = time.perf_counter()
        provisional_id = _request_id(value)
        request: AgentRequest | None = None
        stage_timings: dict[str, float] = {}
        try:
            request = AgentRequest.from_value(value)
            provisional_id = request.request_id
            message = request.message.strip()
            if not message:
                result = self._failed(
                    request.request_id, "empty_message", "Customer message is empty."
                )
            else:
                result = self._handle_valid(request, message, stage_timings)
        except ValueError as exc:
            code = "invalid_requested_intent" if "requested_intent" in str(exc) else "invalid_request"
            result = self._failed(
                provisional_id, code, "The request is invalid and needs human review."
            )
        except Exception:
            result = self._failed(
                provisional_id,
                "unexpected_error",
                "The agent could not safely process this request; human review is required.",
            )
        duration_ms = round((time.perf_counter() - started) * 1000, 3)
        result = replace(
            result,
            processing_metadata={
                **result.processing_metadata,
                "duration_ms": duration_ms,
                "stage_timings_ms": stage_timings,
                "provider_retry_count": None,
                "provider_retry_count_status": "provider_sdk_retries_not_exposed",
                "configured_provider_max_retries": self.config.provider_max_retries,
                "provider_error_category": (
                    result.processing_metadata.get("provider_error_category")
                    or (
                        "malformed_response"
                        if result.error == "malformed_model_output"
                        else "provider_error"
                        if result.error == "provider_failed"
                        else None
                    )
                ),
            },
        )
        logger.info(
            "support_agent_request_complete",
            extra={
                "request_id": result.request_id,
                "intent": result.intent,
                "retrieval_count": len(result.evidence),
                "decision": result.decision.decision,
                "duration_ms": duration_ms,
                "error_category": result.error,
            },
        )
        return result

    def _handle_valid(
        self,
        request: AgentRequest,
        message: str,
        stage_timings: dict[str, float],
    ) -> AgentResponse:
        history = bounded_conversation_history(
            request.conversation_history,
            max_turns=self.config.history_window,
            max_chars=self.config.history_max_chars,
        )
        phase_started = time.perf_counter()
        try:
            intent = self.intent_detector.detect(
                message, history, request.requested_intent
            )
        except ValueError:
            raise
        except Exception:
            return self._failed(
                request.request_id,
                "intent_detection_failed",
                "Intent detection failed; human review is required.",
            )
        finally:
            stage_timings["intent_detection_latency_ms"] = round(
                (time.perf_counter() - phase_started) * 1000, 3
            )

        if intent.name not in INTENT_NAMES:
            return self._failed(
                request.request_id,
                "invalid_intent",
                "Intent detection returned an unsupported category; human review is required.",
                intent=intent,
            )
        if intent.name == "other_unclear":
            return self._escalated(
                request.request_id,
                intent,
                "none",
                "Intent is unclear; no automatic reply was generated.",
            )

        query = build_retrieval_query(message, intent, history)
        phase_started = time.perf_counter()
        try:
            rows = self.retriever.retrieve(query, k=self.config.top_k)
            if not isinstance(rows, list):
                raise ValueError("retriever must return a list")
            evidence = convert_evidence(rows)
        except Exception:
            if intent.name in SENSITIVE_INTENTS:
                return self._failed(
                    request.request_id,
                    "retrieval_failed",
                    "Sensitive intent requires human review; no customer-facing draft was generated.",
                    intent=intent,
                    evidence_reason="Historical retrieval failed; no evidence was available.",
                )
            return self._failed(
                request.request_id,
                "retrieval_failed",
                "Historical retrieval failed; human review is required.",
                intent=intent,
            )
        finally:
            stage_timings["retrieval_latency_ms"] = round(
                (time.perf_counter() - phase_started) * 1000, 3
            )

        phase_started = time.perf_counter()
        try:
            assessment = assess_evidence(
                evidence,
                self.config.minimum_retrieval_similarity,
                expected_intent=intent.name,
            )
        finally:
            stage_timings["evidence_gate_latency_ms"] = round(
                (time.perf_counter() - phase_started) * 1000, 3
            )
        if intent.name in SENSITIVE_INTENTS:
            return self._escalated(
                request.request_id,
                intent,
                assessment.status,
                assessment.reason,
                evidence=assessment.evidence,
                processing_metadata=_retrieval_diagnostics(rows, assessment),
                decision_reason=(
                    "Sensitive intent requires human review; "
                    "no customer-facing draft was generated."
                ),
            )
        if assessment.status != "sufficient":
            return self._escalated(
                request.request_id,
                intent,
                assessment.status,
                assessment.reason,
                evidence=assessment.evidence,
                processing_metadata=_retrieval_diagnostics(rows, assessment),
            )

        phase_started = time.perf_counter()
        generation_evidence = tuple(
            item for item in assessment.evidence
            if item.intent_match is not False
            and item.retrieval_score >= self.config.minimum_retrieval_similarity
            and item.support_response.strip()
        )

        def measured_provider_call(system: str, user: str) -> str:
            provider_started = time.perf_counter()
            try:
                return self.llm_call(system, user)
            finally:
                stage_timings["provider_call_latency_ms"] = round(
                    (time.perf_counter() - provider_started) * 1000, 3
                )

        try:
            retrieved_rows = [
                {
                    "source_id": item.source_id,
                    "amazonhelp_response": item.support_response,
                    "similarity": item.retrieval_score,
                    "score_components": dict(item.score_components),
                }
                for item in generation_evidence
            ]
            reply = generate_reply(
                message,
                intent.name,
                retrieved_rows,
                measured_provider_call,
                conversation_history=history,
            )
            allowed_evidence_ids = {item.source_id for item in generation_evidence}
            if not set(reply["evidence_ids"]).issubset(allowed_evidence_ids):
                raise ReplyGenerationError(
                    "Model output cites evidence that was not supplied"
                )
        except ReplyGenerationError:
            failed = self._failed(
                request.request_id,
                "malformed_model_output",
                "The response provider returned an invalid draft; human review is required.",
                intent=intent,
                evidence=assessment.evidence,
                evidence_status=assessment.status,
                evidence_reason=assessment.reason,
            )
            return replace(
                failed,
                processing_metadata={
                    **_retrieval_diagnostics(rows, assessment),
                    "provider_error_category": "malformed_response",
                },
            )
        except Exception as exc:
            failed = self._failed(
                request.request_id,
                "provider_failed",
                "The response provider failed; human review is required.",
                intent=intent,
                evidence=assessment.evidence,
                evidence_status=assessment.status,
                evidence_reason=assessment.reason,
            )
            return replace(
                failed,
                processing_metadata={
                    **_retrieval_diagnostics(rows, assessment),
                    "provider_error_category": _provider_error_category(exc)
                },
            )
        finally:
            stage_timings["generation_latency_ms"] = round(
                (time.perf_counter() - phase_started) * 1000, 3
            )

        phase_started = time.perf_counter()
        try:
            grounding = validate_grounding(
                reply["draft_reply"],
                generation_evidence,
                self.config.minimum_grounding_token_support,
            )
        except Exception:
            return self._failed(
                request.request_id,
                "grounding_failed",
                "Independent grounding validation failed; human review is required.",
                intent=intent,
                evidence=assessment.evidence,
                evidence_status=assessment.status,
                evidence_reason=assessment.reason,
                processing_metadata=_retrieval_diagnostics(rows, assessment),
                draft_reply=reply["draft_reply"],
                model_confidence=reply["grounding_confidence"],
                needs_human_review=True,
            )
        finally:
            stage_timings["grounding_latency_ms"] = round(
                (time.perf_counter() - phase_started) * 1000, 3
            )

        policy_result = decide_escalation(
            message,
            intent.name,
            grounding_confidence=reply["grounding_confidence"],
            needs_human_review=(
                reply["needs_human_review"]
                or reply["grounding_status"] != "supported"
                or not grounding.supported
                or reply["escalation_required"]
            ),
            confidence_threshold=self.config.escalation_confidence_threshold,
        )
        reason = policy_result["reason"]
        if not grounding.supported:
            reason = f"Independent grounding gate: {grounding.reason}"
        return AgentResponse(
            request_id=request.request_id,
            intent=intent.name,
            intent_confidence=intent.confidence,
            intent_reason=intent.reason,
            intent_source=intent.source,
            evidence=assessment.evidence,
            evidence_status=assessment.status,
            evidence_reason=assessment.reason,
            draft_reply=reply["draft_reply"],
            model_grounding_confidence=reply["grounding_confidence"],
            needs_human_review=(
                reply["needs_human_review"]
                or reply["escalation_required"]
                or reply["grounding_status"] != "supported"
                or not grounding.supported
            ),
            grounding=grounding,
            decision=AgentDecision(policy_result["decision"], reason),
            processing_metadata={
                **_retrieval_diagnostics(rows, assessment),
                "response_contract": {
                    "provider_grounding_status": reply["grounding_status"],
                    "escalation_required": reply["escalation_required"],
                    "evidence_ids": reply["evidence_ids"],
                },
                "grounding_diagnostics": {
                    "grounding_status": (
                        "supported"
                        if grounding.supported
                        else "unsupported_claim"
                        if grounding.unsupported_claims
                        else "insufficient_support"
                    ),
                    "unsupported_claim_detected": bool(
                        grounding.unsupported_claims
                    ),
                    "evidence_token_support_rate": (
                        grounding.evidence_token_support_rate
                    ),
                },
            },
        )

    @staticmethod
    def _failed(
        request_id: str,
        error: str,
        reason: str,
        *,
        intent: AgentIntent | None = None,
        evidence: tuple[AgentEvidence, ...] = (),
        evidence_status: EvidenceStatus = "none",
        evidence_reason: str = "Evidence was not evaluated.",
        draft_reply: str | None = None,
        model_confidence: float | None = None,
        grounding: GroundingResult | None = None,
        needs_human_review: bool = True,
        processing_metadata: Mapping[str, Any] | None = None,
    ) -> AgentResponse:
        return AgentResponse(
            request_id=request_id,
            intent=intent.name if intent else None,
            intent_confidence=intent.confidence if intent else None,
            intent_reason=intent.reason if intent else None,
            intent_source=intent.source if intent else None,
            evidence=evidence,
            evidence_status=evidence_status,
            evidence_reason=evidence_reason,
            draft_reply=draft_reply,
            model_grounding_confidence=model_confidence,
            needs_human_review=needs_human_review,
            grounding=grounding,
            decision=AgentDecision("escalate", reason),
            processing_metadata=processing_metadata or {},
            error=error,
        )

    def _escalated(
        self,
        request_id: str,
        intent: AgentIntent,
        evidence_status: EvidenceStatus,
        evidence_reason: str,
        *,
        evidence: tuple[AgentEvidence, ...] = (),
        decision_reason: str | None = None,
        processing_metadata: Mapping[str, Any] | None = None,
    ) -> AgentResponse:
        return AgentResponse(
            request_id=request_id,
            intent=intent.name,
            intent_confidence=intent.confidence,
            intent_reason=intent.reason,
            intent_source=intent.source,
            evidence=evidence,
            evidence_status=evidence_status,
            evidence_reason=evidence_reason,
            draft_reply=None,
            model_grounding_confidence=None,
            needs_human_review=True,
            grounding=None,
            decision=AgentDecision(
                "escalate", decision_reason or evidence_reason
            ),
            processing_metadata=processing_metadata or {},
        )


def build_retrieval_query(
    message: str,
    intent: AgentIntent,
    history: tuple[str, ...],
) -> str:
    """Build a current-turn-first query; history only disambiguates unclear turns."""
    current = " ".join(unicodedata.normalize("NFC", message).split())
    parts = [
        f"current request: {current}",
        f"intent: {intent.name.replace('_', ' ')}",
    ]
    if intent.source == "conversation_context_fallback" and history:
        recent_context = " ".join(history[-1].split())[:500]
        if recent_context:
            parts.append(f"recent context: {recent_context}")
    return " ".join(parts)


def _retrieval_diagnostics(
    rows: list[dict[str, Any]],
    assessment: EvidenceAssessment,
) -> dict[str, Any]:
    candidates: list[int] = []
    for row in rows:
        candidate_count = row.get("candidate_count")
        if isinstance(candidate_count, int) and not isinstance(candidate_count, bool):
            candidates.append(candidate_count)
    backends = sorted({
        row["retrieval_backend"]
        for row in rows
        if isinstance(row.get("retrieval_backend"), str)
    })
    count_scopes = sorted({
        row["candidate_count_scope"]
        for row in rows
        if isinstance(row.get("candidate_count_scope"), str)
    })
    return {
        "retrieval_diagnostics": {
            "retrieval_backend": backends[0] if len(backends) == 1 else (
                "mixed" if backends else "unknown"
            ),
            "candidate_count": max(candidates, default=len(rows)),
            "candidate_count_scope": (
                count_scopes[0] if len(count_scopes) == 1
                else "mixed" if count_scopes else "returned_rows"
            ),
            "selected_evidence_ids": [item.source_id for item in assessment.evidence],
            "ranking_scores": [
                {
                    "evidence_id": item.source_id,
                    "score": item.retrieval_score,
                    "score_components": dict(item.score_components),
                }
                for item in assessment.evidence
            ],
            "evidence_sufficient": assessment.evidence_sufficient,
            "evidence_conflict": assessment.evidence_conflict,
            "evidence_intent_match": assessment.evidence_intent_match,
            "evidence_resolution_match": assessment.evidence_resolution_match,
            "resolution_match_status": assessment.resolution_match_status,
        }
    }


def _request_id(value: AgentRequest | Mapping[str, Any]) -> str:
    candidate = value.request_id if isinstance(value, AgentRequest) else (
        value.get("request_id") if isinstance(value, Mapping) else None
    )
    if isinstance(candidate, str) and candidate and len(candidate) <= 128 and all(
        char.isalnum() or char in "-_.:" for char in candidate
    ):
        return candidate
    return str(uuid4())


def _provider_error_category(error: Exception) -> str:
    status = getattr(error, "status_code", None)
    if status == 429:
        return "rate_limited"
    if isinstance(status, int) and status >= 500:
        return "provider_server_error"
    if isinstance(error, TimeoutError) or "timeout" in type(error).__name__.lower():
        return "provider_timeout"
    return "provider_error"
