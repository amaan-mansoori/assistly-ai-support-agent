"""Customer registration and bearer-token login."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.errors import PlatformError
from src.api.schemas import TokenOut, UserCreate, UserLogin, UserOut
from src.api.security import hash_password, issue_token, verify_password
from src.db.models import User

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(
    payload: UserCreate, request: Request, session: Session = Depends(get_db)
):
    user = User(email=payload.email, password_hash=hash_password(payload.password), role="customer")
    session.add(user)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise PlatformError(409, "EMAIL_ALREADY_REGISTERED", "An account already exists for this email.") from exc
    session.refresh(user)
    return TokenOut(
        access_token=issue_token(user, request.app.state.settings.jwt_secret),
        expires_in=30 * 60,
        user=UserOut.model_validate(user),
    )


@router.post("/token", response_model=TokenOut)
def login(payload: UserLogin, request: Request, session: Session = Depends(get_db)):
    user = session.scalar(select(User).where(User.email == payload.email.strip().lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise PlatformError(401, "INVALID_CREDENTIALS", "Email or password is incorrect.")
    return TokenOut(
        access_token=issue_token(user, request.app.state.settings.jwt_secret),
        expires_in=30 * 60,
        user=UserOut.model_validate(user),
    )
