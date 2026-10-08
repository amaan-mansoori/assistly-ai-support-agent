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
        text = " ".join((*conversation_history, message)).strip()
        name = classify_intent(message)
        if name == "other_unclear" and conversation_history:
            name = classify_intent(text)
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
            "regex_taxonomy",
        )
