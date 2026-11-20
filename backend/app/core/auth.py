from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import AuthService


def get_token_from_request(request: Request) -> str | None:
    """
    Extract authentication token from:
    1. Authorization: Bearer <token> header
    2. Session HttpOnly cookie
    3. Query parameter 'token' (for media/artifact/report streaming where headers cannot be set)
    """
    settings = get_settings()
    auth_header = request.headers.get("Authorization")
    if auth_header:
        parts = auth_header.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]

    # Check cookie
    cookie_token = request.cookies.get(settings.session_cookie_name)
    if cookie_token:
        return cookie_token

    # Check query param (for raster images, PDF downloads, and direct GIS assets)
    query_token = request.query_params.get("token")
    if query_token and query_token.strip():
        return query_token.strip()

    return None


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency to retrieve the current authenticated active user.
    Validates token from Authorization header or HttpOnly session cookie.
    """
    token = get_token_from_request(request)
    if not token:
        raise AppError(
            "Authentication required.",
            status_code=401,
            code="UNAUTHORIZED",
        )

    auth_service = AuthService(db)
    return auth_service.get_user_by_token(token)


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
) -> User | None:
    """
    Optional authentication dependency. Returns the User if authenticated, else None.
    """
    token = get_token_from_request(request)
    if not token:
        return None

    try:
        auth_service = AuthService(db)
        return auth_service.get_user_by_token(token)
    except AppError:
        return None

