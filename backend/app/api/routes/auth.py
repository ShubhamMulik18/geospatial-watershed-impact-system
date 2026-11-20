from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_token_from_request
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, LogoutResponse, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> LoginResponse:
    settings = get_settings()
    auth_service = AuthService(db)

    user = auth_service.authenticate_user(
        username=payload.username,
        password=payload.password,
    )

    session, raw_token = auth_service.create_session(
        user=user,
        expire_seconds=settings.session_expire_seconds,
    )

    response.set_cookie(
        key=settings.session_cookie_name,
        value=raw_token,
        max_age=settings.session_expire_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/",
    )

    return LoginResponse(
        user=UserResponse.model_validate(user),
        access_token=raw_token,
        token_type="bearer",
        expires_in=settings.session_expire_seconds,
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> LogoutResponse:
    settings = get_settings()
    token = get_token_from_request(request)
    if token:
        AuthService(db).revoke_session(token)

    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
    )

    return LogoutResponse(message="Logged out successfully")


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)

