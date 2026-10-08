"""Customer feedback persistence and ownership enforcement."""
from sqlalchemy.orm import Session

from src.api.errors import PlatformError
from src.api.security import Principal
from src.db.models import AgentRun, Conversation, Feedback


class FeedbackService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        principal: Principal,
        *,
        conversation_id: str | None,
        agent_run_id: str | None,
        rating: int,
        category: str | None,
        comment: str | None,
    ) -> Feedback:
        if conversation_id is None and agent_run_id is None:
            raise PlatformError(422, "FEEDBACK_TARGET_REQUIRED", "Provide a conversation_id or agent_run_id.")
        run = self.session.get(AgentRun, agent_run_id) if agent_run_id else None
        if agent_run_id and run is None:
            raise PlatformError(404, "AGENT_RUN_NOT_FOUND", "Agent run was not found.")
        if run is not None:
            if conversation_id and conversation_id != run.conversation_id:
                raise PlatformError(422, "FEEDBACK_TARGET_MISMATCH", "The feedback targets do not match.")
            conversation_id = run.conversation_id
        conversation = (
            self.session.get(Conversation, conversation_id) if conversation_id else None
        )
        if conversation is None or conversation.user_id != principal.id:
            raise PlatformError(404, "CONVERSATION_NOT_FOUND", "Conversation was not found.")
        feedback = Feedback(
            conversation_id=conversation.id,
            agent_run_id=run.id if run else None,
            user_id=principal.id,
            rating=rating,
            category=category,
            comment=comment,
        )
        self.session.add(feedback)
        self.session.commit()
        self.session.refresh(feedback)
        return feedback
