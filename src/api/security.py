"""Password hashing and short-lived signed bearer tokens."""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.errors import PlatformError
from src.db.models import User

TOKEN_TTL_SECONDS = 30 * 60
PBKDF2_ITERATIONS = 310_000
_DUMMY_SALT = b"support-agent-auth-check"
_DUMMY_HASH = hashlib.pbkdf2_hmac(
    "sha256", b"not-a-real-account-password", _DUMMY_SALT, PBKDF2_ITERATIONS
)
_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    id: str
    email: str | None
    role: str


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS,
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, encoded: str | None) -> bool:
    if not encoded:
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), _DUMMY_SALT, PBKDF2_ITERATIONS
        )
        hmac.compare_digest(candidate, _DUMMY_HASH)
        return False
    try:
        algorithm, count, salt_value, digest_value = encoded.split("$", 3)
        iterations = int(count)
        if algorithm != "pbkdf2_sha256" or not 100_000 <= iterations <= 2_000_000:
            return False
        salt = base64.urlsafe_b64decode(salt_value.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_value.encode("ascii"))
    except (ValueError, TypeError):
        salt = _DUMMY_SALT
        expected = _DUMMY_HASH
        iterations = PBKDF2_ITERATIONS
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def issue_token(user: User, secret: str) -> str:
    payload = {
        "sub": user.id,
        "exp": int(datetime.now(UTC).timestamp()) + TOKEN_TTL_SECONDS,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str, secret: str) -> str:
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"require": ["sub", "exp"]},
        )
        user_id = payload["sub"]
        if not isinstance(user_id, str):
            raise InvalidTokenError("subject must be a string")
        return user_id
    except InvalidTokenError as exc:
        raise PlatformError(401, "INVALID_TOKEN", "Authentication is required.") from exc


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: Session = Depends(get_db),
) -> Principal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise PlatformError(401, "AUTHENTICATION_REQUIRED", "Authentication is required.")
    user_id = decode_token(credentials.credentials, request.app.state.settings.jwt_secret)
    user = session.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise PlatformError(401, "INVALID_TOKEN", "Authentication is required.")
    return Principal(id=user.id, email=user.email, role=user.role)


def require_roles(*roles: str):
    def dependency(principal: Principal = Depends(get_current_user)) -> Principal:
        if principal.role not in roles:
            raise PlatformError(403, "FORBIDDEN", "You do not have permission to perform this action.")
        return principal

    return dependency
