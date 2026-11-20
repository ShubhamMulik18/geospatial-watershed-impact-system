from datetime import datetime, timedelta, timezone
import re
import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)
from app.models.user import User
from app.models.user_session import UserSession


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()

    def authenticate_user(self, username: str, password: str) -> User:
        """Authenticate user by username and password."""
        cleaned_username = username.strip() if username else ""
        if not cleaned_username or not password:
            raise AppError(
                "Username and password are required.",
                status_code=401,
                code="INVALID_CREDENTIALS",
            )

        user = (
            self.db.query(User)
            .filter(func.lower(User.username) == func.lower(cleaned_username))
            .first()
        )

        if not user or not verify_password(password, user.password_hash):
            raise AppError(
                "Invalid username or password.",
                status_code=401,
                code="INVALID_CREDENTIALS",
            )

        if not user.is_active:
            raise AppError(
                "Account is inactive. Please contact an administrator.",
                status_code=403,
                code="ACCOUNT_INACTIVE",
            )

        return user

    def create_session(
        self,
        user: User,
        expire_seconds: int | None = None,
    ) -> tuple[UserSession, str]:
        """Create a new database-backed session for a user and return the raw session token."""
        duration = expire_seconds or self.settings.session_expire_seconds
        raw_token = generate_session_token()
        token_hash = hash_session_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=duration)

        session = UserSession(
            id=uuid.uuid4(),
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session, raw_token

    def get_user_by_token(self, token: str) -> User:
        """Retrieve and validate the active user corresponding to a session token."""
        if not token or not token.strip():
            raise AppError(
                "Authentication token is required.",
                status_code=401,
                code="UNAUTHORIZED",
            )

        token_hash = hash_session_token(token.strip())
        session = (
            self.db.query(UserSession)
            .filter(UserSession.token_hash == token_hash)
            .first()
        )

        if not session:
            raise AppError(
                "Invalid or expired authentication session.",
                status_code=401,
                code="INVALID_SESSION",
            )

        if session.is_revoked:
            raise AppError(
                "Session has been revoked or logged out.",
                status_code=401,
                code="SESSION_REVOKED",
            )

        # Check expiration
        now_utc = datetime.now(timezone.utc)
        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at <= now_utc:
            raise AppError(
                "Session has expired. Please log in again.",
                status_code=401,
                code="SESSION_EXPIRED",
            )

        user = session.user
        if not user or not user.is_active:
            raise AppError(
                "Account is inactive or not found.",
                status_code=403,
                code="ACCOUNT_INACTIVE",
            )

        return user

    def revoke_session(self, token: str) -> bool:
        """Revoke a session by token hash."""
        if not token:
            return False

        token_hash = hash_session_token(token.strip())
        session = (
            self.db.query(UserSession)
            .filter(UserSession.token_hash == token_hash)
            .first()
        )
        if session:
            session.is_revoked = True
            self.db.commit()
            return True
        return False

    def create_user(
        self,
        username: str,
        password: str,
        is_active: bool = True,
    ) -> User:
        """Create a new user with secure password hashing and validation."""
        cleaned_username = username.strip() if username else ""

        if not re.match(r"^[a-zA-Z0-9_\-\.]{3,64}$", cleaned_username):
            raise AppError(
                "Username must be between 3 and 64 characters long and contain only letters, numbers, hyphens, dots, or underscores.",
                status_code=400,
                code="INVALID_USERNAME",
            )

        if not password or len(password) < 8:
            raise AppError(
                "Password must be at least 8 characters long.",
                status_code=400,
                code="INVALID_PASSWORD",
            )

        existing = (
            self.db.query(User)
            .filter(func.lower(User.username) == func.lower(cleaned_username))
            .first()
        )
        if existing:
            raise AppError(
                f"Username '{cleaned_username}' already exists.",
                status_code=409,
                code="DUPLICATE_USERNAME",
            )

        user = User(
            id=uuid.uuid4(),
            username=cleaned_username,
            password_hash=hash_password(password),
            is_active=is_active,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

