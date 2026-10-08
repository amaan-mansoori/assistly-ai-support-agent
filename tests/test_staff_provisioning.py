import pytest

from src.db.database import Base, make_engine, make_session_factory
from src.platform.provision_user import create_staff_user


@pytest.fixture
def session(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'staff.sqlite'}")
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    with factory() as connection:
        yield connection
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_staff_provisioning_normalizes_email_and_hashes_password(session):
    user = create_staff_user(session, " AGENT@EXAMPLE.COM ", "agent", "very-secure-password")

    assert user.email == "agent@example.com"
    assert user.role == "agent"
    assert user.password_hash != "very-secure-password"


def test_staff_provisioning_rejects_customer_role_and_duplicate(session):
    with pytest.raises(ValueError, match="Only agent and admin"):
        create_staff_user(session, "customer@example.com", "customer", "very-secure-password")
    create_staff_user(session, "admin@example.com", "admin", "very-secure-password")

    with pytest.raises(ValueError, match="already exists"):
        create_staff_user(session, "ADMIN@example.com", "agent", "very-secure-password")
