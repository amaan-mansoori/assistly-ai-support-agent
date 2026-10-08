"""Database-backed support analytics; empty data returns null rates, not fabricated values."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db.models import AgentRun, Conversation, Feedback, HumanReviewTicket


class AnalyticsService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def summary(self) -> dict:
        total = self.session.scalar(select(func.count()).select_from(Conversation)) or 0
        run_total = self.session.scalar(select(func.count()).select_from(AgentRun)) or 0
        auto_count = self.session.scalar(
            select(func.count()).select_from(AgentRun).where(AgentRun.decision == "auto_handle")
        ) or 0
        escalation_count = run_total - auto_count
        resolved = self.session.scalar(
            select(func.count()).select_from(HumanReviewTicket).where(
                HumanReviewTicket.status.in_(("resolved", "closed"))
            )
        ) or 0
        ticket_total = self.session.scalar(
            select(func.count()).select_from(HumanReviewTicket)
        ) or 0
        average_latency = self.session.scalar(select(func.avg(AgentRun.latency_ms)))
        average_rating = self.session.scalar(select(func.avg(Feedback.rating)))
        intents = self.session.execute(
            select(AgentRun.intent, func.count())
            .where(AgentRun.intent.is_not(None))
            .group_by(AgentRun.intent)
        ).all()
        errors = self.session.execute(
            select(AgentRun.error_category, func.count())
            .where(AgentRun.error_category.is_not(None))
            .group_by(AgentRun.error_category)
        ).all()
        return {
            "total_conversations": int(total),
            "auto_handle_rate": auto_count / run_total if run_total else None,
            "escalation_rate": escalation_count / run_total if run_total else None,
            "resolution_rate": resolved / ticket_total if ticket_total else None,
            "average_latency_ms": float(average_latency) if average_latency is not None else None,
            "average_feedback_rating": float(average_rating) if average_rating is not None else None,
            "intent_distribution": {name: int(count) for name, count in intents},
            "error_categories": {name: int(count) for name, count in errors},
        }
