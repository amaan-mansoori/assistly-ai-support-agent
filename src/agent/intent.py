"""Adapter around the repository's canonical deterministic intent taxonomy."""
from __future__ import annotations

from src.intents.final_taxonomy_audit import INTENTS, classify_intent
from src.agent.models import AgentIntent

INTENT_NAMES = frozenset((*INTENTS.keys(), "other_unclear"))


class IntentDetector:
    def detect(
        self,
        message: str,
        conversation_history: tuple[str, ...] = (),
        requested_intent: str | None = None,
    ) -> AgentIntent:
        if requested_intent is not None:
            if requested_intent not in INTENT_NAMES:
                raise ValueError("requested_intent is not in the supported taxonomy")
        name = classify_intent(message)
        source = "regex_taxonomy"
        if name == "other_unclear" and conversation_history:
            context_first = " ".join((*conversation_history, message)).strip()
            context_last = " ".join((message, *reversed(conversation_history))).strip()
            name = classify_intent(context_first)
            if name == "other_unclear":
                name = classify_intent(context_last)
            if name != "other_unclear":
                source = "conversation_context_fallback"
        if requested_intent is not None and requested_intent != name:
            return AgentIntent(
                "other_unclear",
                None,
                "Caller intent suggestion conflicts with the local taxonomy; human review is required.",
                "taxonomy_conflict",
            )
        return AgentIntent(
            name,
            None,
            "Deterministic ordered regex taxonomy; no calibrated confidence is available.",
            source,
        )
