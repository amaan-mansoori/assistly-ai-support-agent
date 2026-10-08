"""Interactively provision a support agent or administrator account."""
from __future__ import annotations

import argparse
from getpass import getpass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.api.schemas import UserCreate
from src.api.security import hash_password
from src.db.database import make_engine, make_session_factory
from src.db.models import User
from src.platform.config import PlatformSettings


def create_staff_user(
    session: Session,
    email: str,
    role: str,
    password: str,
) -> User:
    if role not in {"agent", "admin"}:
        raise ValueError("Only agent and admin roles may be provisioned.")
    payload = UserCreate(email=email, password=password)
    if session.scalar(select(User.id).where(User.email == payload.email)) is not None:
        raise ValueError("An account already exists for this email.")
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=role,
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ValueError("An account already exists for this email.") from exc
    session.refresh(user)
    return user


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--role", required=True, choices=("agent", "admin"))
    args = parser.parse_args()
    password = getpass("New password (12+ characters): ")
    confirmation = getpass("Confirm password: ")
    if password != confirmation:
        parser.error("Passwords do not match.")

    settings = PlatformSettings.from_env()
    engine = make_engine(settings.database_url)
    try:
        with make_session_factory(engine)() as session:
            user = create_staff_user(session, args.email, args.role, password)
    except ValueError as exc:
        parser.error(str(exc))
    finally:
        engine.dispose()
    print(f"Provisioned {user.role} account {user.email}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
