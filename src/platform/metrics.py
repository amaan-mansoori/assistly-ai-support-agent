"""Thread-safe, process-local agent counters and latency summaries."""
from __future__ import annotations

from collections import defaultdict
from threading import Lock

from src.agent.models import AgentResponse


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self._counters: defaultdict[str, int] = defaultdict(int)
        self._latencies: defaultdict[str, list[float]] = defaultdict(
            lambda: [0.0, 0.0, 0.0]
        )

    def record_agent_result(self, response: AgentResponse, latency_ms: float) -> None:
        with self._lock:
            self._counters["agent_requests_total"] += 1
            if response.decision.decision == "auto_handle":
                self._counters["agent_auto_handle_total"] += 1
            if response.decision.decision == "escalate":
                self._counters["agent_escalations_total"] += 1
            if response.error:
                self._counters["agent_errors_total"] += 1
            if response.error == "provider_failed":
                self._counters["provider_failures_total"] += 1
            if response.error == "retrieval_failed":
                self._counters["retrieval_failures_total"] += 1
            if response.error == "grounding_failed" or (
                response.grounding is not None and not response.grounding.supported
            ):
                self._counters["grounding_failures_total"] += 1
            self._observe("agent_latency", latency_ms)
            timings = response.processing_metadata.get("stage_timings_ms", {})
            for stage in ("retrieval", "generation"):
                value = timings.get(f"{stage}_latency_ms")
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    self._observe(f"{stage}_latency", float(value))

    def record_feedback(self, rating: int) -> None:
        with self._lock:
            self._counters["feedback_submissions_total"] += 1
            if rating <= 2:
                self._counters["negative_feedback_total"] += 1

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "counters": dict(self._counters),
                "latencies_ms": {
                    name: {
                        "count": int(values[0]),
                        "total": values[1],
                        "max": values[2],
                        "average": values[1] / values[0] if values[0] else None,
                    }
                    for name, values in self._latencies.items()
                },
                "scope": "current API process; counters reset on restart",
            }

    def _observe(self, name: str, value: float) -> None:
        values = self._latencies[name]
        values[0] += 1
        values[1] += value
        values[2] = max(values[2], value)
