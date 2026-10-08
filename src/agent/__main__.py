"""Local command-line entrypoint for the support-agent core."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.agent.config import AgentConfig
from src.agent.models import AgentDecision, AgentRequest, AgentResponse
from src.agent.orchestrator import SupportAgent
from src.retrieval.historical_retriever import HistoricalRetriever


def _mock_call(_system: str, prompt: str) -> str:
    marker = "Historical evidence (not instructions):\n"
    evidence_text = prompt.partition(marker)[2]
    records: list[dict[str, Any]] = json.loads(evidence_text) if evidence_text else []
    draft = (
        str(records[0].get("historical_amazonhelp_response", "")).strip()
        if records
        else ""
    )
    if not draft:
        draft = "A support specialist should review this request."
    return json.dumps(
        {
            "draft_reply": draft,
            "grounding_confidence": 0.8,
            "needs_human_review": False,
            "reason": "Local mock provider copied a retrieved historical reply.",
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local customer-support agent.")
    parser.add_argument("--message", help="Customer message; prompts interactively if omitted.")
    parser.add_argument(
        "--history",
        nargs="*",
        default=(),
        help="Earlier customer conversation turns, in chronological order.",
    )
    parser.add_argument("--request-id", help="Optional safe correlation identifier.")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use a local mock that copies a retrieved historical response; no model API call.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="YAML configuration path (defaults to configs/default.yaml).",
    )
    args = parser.parse_args()
    message = args.message if args.message is not None else input("Customer message: ")
    try:
        config = AgentConfig.load(args.config) if args.config else AgentConfig.load()
        retriever, _ = HistoricalRetriever.build()
        if args.mock:
            llm_call = _mock_call
        else:
            from src.agent.reply_generator import configured_llm_call

            llm_call = configured_llm_call(
                config.provider,
                config.model,
                timeout_seconds=config.provider_timeout_seconds,
                max_retries=config.provider_max_retries,
            )
        agent = SupportAgent(retriever, llm_call, config)
        result = agent.handle(
            AgentRequest(
                message=message,
                conversation_history=tuple(args.history),
                request_id=args.request_id or str(uuid4()),
            )
        )
    except Exception:
        request_id = args.request_id or str(uuid4())
        result = AgentResponse(
            request_id=request_id,
            intent=None,
            intent_confidence=None,
            intent_reason=None,
            intent_source=None,
            evidence=(),
            evidence_status="none",
            evidence_reason="The local agent could not initialize its data or provider.",
            draft_reply=None,
            model_grounding_confidence=None,
            needs_human_review=True,
            grounding=None,
            decision=AgentDecision(
                "escalate",
                "Local agent initialization failed; human review is required.",
            ),
            error="initialization_failed",
        )
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
