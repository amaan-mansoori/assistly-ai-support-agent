from datetime import UTC, datetime, timedelta

from src.db.database import Base, make_engine, make_session_factory
from src.db.models import Conversation, Message, User
from src.platform.retention import purge_conversations


def test_retention_previews_and_deletes_old_conversation_cascade(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'retention.sqlite'}")
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    try:
        with factory() as session:
            user = User(email="retention@example.com", role="customer")
            session.add(user)
            session.flush()
            conversation = Conversation(user_id=user.id, status="open", metadata_json={})
            session.add(conversation)
            session.flush()
            message = Message(
                conversation_id=conversation.id,
                sender_type="customer",
                content="Old request",
                metadata_json={},
            )
            session.add(message)
            old_id = conversation.id
            conversation.created_at = datetime.now(UTC) - timedelta(days=90)
            session.commit()
            message_id = message.id

            cutoff = datetime.now(UTC) - timedelta(days=30)
            assert purge_conversations(session, older_than=cutoff) == 1
            assert session.get(Conversation, old_id) is not None
            assert purge_conversations(session, older_than=cutoff, apply=True) == 1
            session.expire_all()
            assert session.get(Conversation, old_id) is None
            assert session.get(Message, message_id) is None
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
