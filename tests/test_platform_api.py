from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.agent.models import (
    AgentDecision,
    AgentEvidence,
    AgentResponse,
    DecisionKind,
    GroundingResult,
)
from src.api.main import create_app
from src.api.security import hash_password
from src.db.database import Base, make_engine, make_session_factory
from src.db.models import User
from src.platform.config import PlatformSettings
from src.platform.rate_limit import FixedWindowLimiter


class StubAgent:
    def __init__(
        self,
        decision: DecisionKind = "auto_handle",
        fail: bool = False,
        intent: str = "delivery_status_delay",
        generated: bool = True,
    ):
        self.decision: DecisionKind = decision
        self.fail = fail
        self.intent = intent
        self.generated = generated
        self.calls = []

    def handle(self, value):
        self.calls.append(value)
        if self.fail:
            raise RuntimeError("private provider failure")
        is_auto = self.decision == "auto_handle"
        return AgentResponse(
            request_id=value["request_id"],
            intent=self.intent,
            intent_confidence=None,
            intent_reason="test taxonomy",
            intent_source="test",
            evidence=(
                AgentEvidence(
                    "An older late order",
                    "Please check tracking for updates.",
                    "source-1",
                    0.9,
                ),
            ),
            evidence_status="sufficient",
            evidence_reason="test evidence",
            model_grounding_confidence=0.9 if is_auto and self.generated else None,
            needs_human_review=not is_auto,
            grounding=(
                GroundingResult(
                    supported=is_auto,
                    score=1.0 if is_auto else 0.0,
                    evidence_token_support_rate=1.0 if is_auto else 0.0,
                    unsupported_claims=(),
                    reason="test grounding",
                )
                if self.generated
                else None
            ),
            draft_reply=(
                (
                    "This draft is for internal human review."
                    if not is_auto
                    else "Please check tracking for updates."
                )
                if self.generated
                else None
            ),
            decision=AgentDecision(
                self.decision,
                "test escalation reason" if not is_auto else "test auto decision",
            ),
            processing_metadata={
                "duration_ms": 5.0,
                "stage_timings_ms": {
                    "retrieval_latency_ms": 2.0,
                    **({"generation_latency_ms": 3.0} if self.generated else {}),
                },
            },
        )


@pytest.fixture
def platform(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'platform.sqlite'}"
    engine = make_engine(database_url)
    Base.metadata.create_all(engine)
    session_factory = make_session_factory(engine)
    auto_agent = StubAgent()
    app = create_app(
        PlatformSettings(
            app_env="test",
            database_url=database_url,
            redis_url=None,
            jwt_secret="test-signing-secret-with-more-than-32-bytes",
            log_level="WARNING",
            cors_origins=("http://localhost:3000",),
            conversation_history_window=2,
            conversation_history_max_chars=100,
        ),
        session_factory=session_factory,
        agent_factory=lambda: auto_agent,
    )
    with TestClient(app) as client:
        yield client, session_factory, auto_agent
    engine.dispose()


def register(client: TestClient, email="customer@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "secure-test-password"},
    )
    assert response.status_code == 201, response.text
    result = response.json()
    return result["access_token"], result["user"]["id"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_register_login_and_authentication_errors_are_safe(platform):
    client, _sessions, _agent = platform
    _token, _user_id = register(client)
    login = client.post(
        "/api/v1/auth/token",
        json={"email": "CUSTOMER@example.com", "password": "secure-test-password"},
    )
    bad_login = client.post(
        "/api/v1/auth/token",
        json={"email": "customer@example.com", "password": "wrong-password"},
    )
    unauthorized = client.get("/api/v1/conversations")

    assert login.status_code == 200
    assert login.json()["user"]["id"] == _user_id
    assert bad_login.status_code == 401
    assert "wrong-password" not in bad_login.text
    assert unauthorized.status_code == 401
    assert unauthorized.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_conversation_message_idempotency_and_history(platform):
    client, _sessions, agent = platform
    token, owner_id = register(client)
    headers = {**auth(token), "Idempotency-Key": "message-key-001"}
    created = client.post(
        "/api/v1/conversations", json={"metadata": {"channel": "web"}}, headers=auth(token)
    )
    conversation_id = created.json()["id"]
    first = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "My order is late."},
        headers=headers,
    )
    repeated = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "My order is late."},
        headers=headers,
    )
    messages = client.get(
        f"/api/v1/conversations/{conversation_id}/messages", headers=auth(token)
    )
    listing = client.get("/api/v1/conversations", headers=auth(token))

    assert created.status_code == 201
    assert created.json()["metadata"] == {"channel": "web"}
    assert first.status_code == 200
    assert first.json()["status"] == "auto_handle"
    assert first.json()["assistant_message"]["content"] == "Please check tracking for updates."
    assert repeated.json()["agent_run"]["id"] == first.json()["agent_run"]["id"]
    assert len(agent.calls) == 1
    assert len(messages.json()) == 2
    assert listing.json()[0]["id"] == conversation_id
    assert agent.calls[0]["conversation_history"] == ()
    assert owner_id


def test_persisted_agent_context_uses_only_the_configured_recent_window(platform):
    client, _sessions, agent = platform
    token, _owner_id = register(client)
    conversation = client.post(
        "/api/v1/conversations", json={}, headers=auth(token)
    ).json()

    for index, content in enumerate(("first message", "second message", "third message")):
        response = client.post(
            f"/api/v1/conversations/{conversation['id']}/messages",
            json={"content": content},
            headers={**auth(token), "Idempotency-Key": f"history-window-{index}"},
        )
        assert response.status_code == 200

    assert agent.calls[-1]["conversation_history"] == (
        "second message",
        "Please check tracking for updates.",
    )


def test_idempotency_conflict_rejects_different_payload(platform):
    client, _sessions, _agent = platform
    token, _ = register(client)
    conversation = client.post("/api/v1/conversations", headers=auth(token), json={}).json()
    headers = {**auth(token), "Idempotency-Key": "same-key"}
    client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"content": "First content"},
    )
    conflict = client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"content": "Different content"},
    )

    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"


def test_customer_cannot_read_other_conversation_or_use_staff_routes(platform):
    client, _sessions, _agent = platform
    first_token, _ = register(client, "first@example.com")
    second_token, _ = register(client, "second@example.com")
    conversation = client.post(
        "/api/v1/conversations", headers=auth(first_token), json={}
    ).json()

    hidden = client.get(
        f"/api/v1/conversations/{conversation['id']}", headers=auth(second_token)
    )
    ticket_list = client.get("/api/v1/tickets", headers=auth(first_token))
    analytics = client.get("/api/v1/analytics", headers=auth(first_token))
    metrics = client.get("/api/v1/metrics", headers=auth(first_token))

    assert hidden.status_code == 404
    assert ticket_list.status_code == 403
    assert analytics.status_code == 403
    assert metrics.status_code == 403


def test_escalation_persists_ticket_and_staff_can_assign_start_resolve(platform):
    client, sessions, _auto_agent = platform
    escalated_agent = StubAgent(decision="escalate")
    client.app.state.agent_factory = lambda: escalated_agent
    token, owner_id = register(client)
    conversation = client.post(
        "/api/v1/conversations", headers=auth(token), json={}
    ).json()
    response = client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers={**auth(token), "Idempotency-Key": "escalate-001"},
        json={"content": "My order needs a person to review this."},
    )
    agent_token, _ = register(client, "other-customer@example.com")
    # The second account remains a customer. Promote only in the test database.
    with sessions() as session:
        user = session.query(User).filter_by(email="other-customer@example.com").one()
        user.role = "agent"
        session.commit()
        agent_id = user.id
    agent_token = client.post(
        "/api/v1/auth/token",
        json={"email": "other-customer@example.com", "password": "secure-test-password"},
    ).json()["access_token"]
    ticket_id = response.json()["ticket_id"]
    queue = client.get("/api/v1/tickets", headers=auth(agent_token))
    agent_conversations = client.get(
        "/api/v1/conversations", headers=auth(agent_token)
    )
    assignment = client.post(
        f"/api/v1/tickets/{ticket_id}/assign",
        headers=auth(agent_token),
        json={"assigned_to": agent_id},
    )
    detail = client.get(f"/api/v1/tickets/{ticket_id}", headers=auth(agent_token))
    started = client.post(f"/api/v1/tickets/{ticket_id}/start", headers=auth(agent_token))
    resolved = client.post(
        f"/api/v1/tickets/{ticket_id}/resolve",
        headers=auth(agent_token),
        json={"resolution_metadata": {"outcome": "tracking guidance provided"}},
    )
    history = client.get(
        f"/api/v1/conversations/{conversation['id']}", headers=auth(token)
    )

    assert response.status_code == 200
    assert response.json()["agent_run"]["decision"] == "escalate"
    assert response.json()["agent_run"]["escalation_reason"] == "test escalation reason"
    assert response.json()["agent_run"]["conversation_id"] == conversation["id"]
    assert response.json()["agent_run"]["intent_reason"] == "test taxonomy"
    assert response.json()["agent_run"]["intent_source"] == "test"
    assert response.json()["agent_run"]["provider"] == "gemini"
    assert response.json()["agent_run"]["processing_metadata"]["stage_timings_ms"][
        "retrieval_latency_ms"
    ] == 2
    assert "draft_reply" not in response.json()["agent_run"]
    assert queue.status_code == 200 and len(queue.json()) == 1
    assert agent_conversations.status_code == 200
    assert [item["id"] for item in agent_conversations.json()] == [conversation["id"]]
    assert assignment.status_code == 200 and assignment.json()["status"] == "assigned"
    assert detail.status_code == 200 and detail.json()["agent_run"]["evidence"]
    assert detail.json()["agent_run"]["draft_reply"] == "This draft is for internal human review."
    assert detail.json()["agent_run"]["evidence_reason"] == "test evidence"
    assert detail.json()["agent_run"]["intent_confidence"] is None
    assert detail.json()["agent_run"]["model"] == "gemini-2.0-flash"
    assert response.json().get("assistant_message") is None
    assert started.status_code == 200 and started.json()["status"] == "in_progress"
    assert resolved.status_code == 200 and resolved.json()["status"] == "resolved"
    assert history.json()["status"] == "resolved"
    assert owner_id


def test_sensitive_ticket_records_that_provider_was_not_invoked(platform):
    client, _sessions, _auto_agent = platform
    sensitive_agent = StubAgent(
        decision="escalate",
        intent="account_access_security",
        generated=False,
    )
    client.app.state.agent_factory = lambda: sensitive_agent
    token, _ = register(client)
    conversation = client.post(
        "/api/v1/conversations", headers=auth(token), json={}
    ).json()
    response = client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers={**auth(token), "Idempotency-Key": "sensitive-no-provider"},
        json={"content": "I cannot access my hacked account."},
    )

    assert response.status_code == 200
    agent_run = response.json()["agent_run"]
    assert agent_run["decision"] == "escalate"
    assert agent_run["provider"] is None
    assert agent_run["model"] is None
    assert response.json().get("assistant_message") is None


def test_feedback_is_private_and_analytics_are_database_backed(platform):
    client, _sessions, _agent = platform
    token, _ = register(client)
    conversation = client.post(
        "/api/v1/conversations", headers=auth(token), json={}
    ).json()
    message = client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers={**auth(token), "Idempotency-Key": "feedback-run-1"},
        json={"content": "My order is late."},
    ).json()
    run_id = message["agent_run"]["id"]
    feedback = client.post(
        "/api/v1/feedback",
        headers=auth(token),
        json={"agent_run_id": run_id, "rating": 5, "category": "helpful"},
    )
    analytics_user_token, _ = register(client, "admin-candidate@example.com")
    with _sessions() as session:
        user = session.query(User).filter_by(email="admin-candidate@example.com").one()
        user.role = "admin"
        session.commit()
    admin_token = client.post(
        "/api/v1/auth/token",
        json={
            "email": "admin-candidate@example.com",
            "password": "secure-test-password",
        },
    ).json()["access_token"]
    analytics = client.get("/api/v1/analytics", headers=auth(admin_token))
    metrics = client.get("/api/v1/metrics", headers=auth(admin_token))

    assert feedback.status_code == 201
    assert feedback.json()["rating"] == 5
    assert analytics.status_code == 200
    assert analytics.json()["total_conversations"] == 1
    assert metrics.status_code == 200
    assert metrics.json()["counters"]["agent_requests_total"] == 1
    assert metrics.json()["counters"]["agent_auto_handle_total"] == 1
    assert metrics.json()["counters"]["feedback_submissions_total"] == 1
    assert metrics.json()["latencies_ms"]["agent_latency"]["count"] == 1
    assert analytics.json()["auto_handle_rate"] == 1.0
    assert analytics.json()["average_feedback_rating"] == 5.0
    assert analytics_user_token


def test_message_validation_and_missing_idempotency_key_return_consistent_errors(platform):
    client, _sessions, _agent = platform
    token, _ = register(client)
    conversation = client.post(
        "/api/v1/conversations", headers=auth(token), json={}
    ).json()
    missing_key = client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers=auth(token),
        json={"content": "A message"},
    )
    invalid = client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers={**auth(token), "Idempotency-Key": "invalid"},
        json={"content": "   "},
    )

    assert missing_key.status_code == 400
    assert missing_key.json()["error"]["code"] == "IDEMPOTENCY_KEY_REQUIRED"
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"


def test_agent_respond_endpoint_reuses_conversation_workflow(platform):
    client, _sessions, agent = platform
    token, _ = register(client)
    conversation = client.post(
        "/api/v1/conversations", headers=auth(token), json={}
    ).json()
    response = client.post(
        "/api/v1/agent/respond",
        headers={**auth(token), "Idempotency-Key": "agent-route-1"},
        json={
            "conversation_id": conversation["id"],
            "message": "My order is late.",
        },
    )

    assert response.status_code == 200
    assert response.json()["agent_run"]["decision"] == "auto_handle"
    assert response.json()["assistant_message"]["content"]
    assert len(agent.calls) == 1


def test_rate_limiting_protects_message_creation(platform):
    client, _sessions, _agent = platform
    client.app.state.rate_limiter = FixedWindowLimiter(
        limit=1, clock=lambda: 600.0
    )
    token, _ = register(client)
    conversation = client.post(
        "/api/v1/conversations", headers=auth(token), json={}
    ).json()
    endpoint = f"/api/v1/conversations/{conversation['id']}/messages"
    first = client.post(
        endpoint,
        headers={**auth(token), "Idempotency-Key": "rate-1"},
        json={"content": "My order is late."},
    )
    limited = client.post(
        endpoint,
        headers={**auth(token), "Idempotency-Key": "rate-2"},
        json={"content": "Another message."},
    )

    assert first.status_code == 200
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_cors_allows_only_configured_local_frontend(platform):
    client, _sessions, _agent = platform
    allowed = client.options(
        "/api/v1/conversations",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,idempotency-key",
        },
    )
    blocked = client.options(
        "/api/v1/conversations",
        headers={
            "Origin": "https://attacker.invalid",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert "access-control-allow-origin" not in blocked.headers
