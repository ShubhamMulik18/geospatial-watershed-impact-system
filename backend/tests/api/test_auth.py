from datetime import datetime, timedelta, timezone
import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.main import app
from app.models.user import User
from app.models.user_session import UserSession
from app.services.auth_service import AuthService


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_user(db_session):
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    password = "TestPassword123!"
    auth_service = AuthService(db_session)
    user = auth_service.create_user(username=username, password=password)
    return user, username, password


def test_unauthenticated_request_to_protected_route_is_rejected(client: TestClient) -> None:
    response = client.get("/api/datasets")
    assert response.status_code == 401
    assert "Authentication required" in response.json()["error"]["message"]


def test_login_success_sets_cookie_and_returns_token(client: TestClient, test_user) -> None:
    _, username, password = test_user
    settings = get_settings()

    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["username"] == username
    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == settings.session_expire_seconds

    # Verify HttpOnly cookie
    assert settings.session_cookie_name in response.cookies
    cookie_value = response.cookies[settings.session_cookie_name]
    assert cookie_value == data["access_token"]


def test_login_invalid_password_returns_401(client: TestClient, test_user) -> None:
    _, username, _ = test_user

    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "WrongPassword456!"},
    )

    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["error"]["message"]


def test_login_unknown_user_returns_401(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "nonexistent_user", "password": "SomePassword123!"},
    )

    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["error"]["message"]


def test_login_inactive_user_returns_403(client: TestClient, db_session) -> None:
    username = f"inactive_{uuid.uuid4().hex[:8]}"
    password = "InactivePassword123!"
    auth_service = AuthService(db_session)
    auth_service.create_user(username=username, password=password, is_active=False)

    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )

    assert response.status_code == 403
    assert "inactive" in response.json()["error"]["message"].lower()


def test_duplicate_username_creation_fails(db_session, test_user) -> None:
    _, username, password = test_user
    auth_service = AuthService(db_session)

    with pytest.raises(Exception) as exc_info:
        auth_service.create_user(username=username, password="AnotherPassword123!")

    assert "already exists" in str(exc_info.value)


def test_authenticated_access_via_cookie(client: TestClient, test_user) -> None:
    _, username, password = test_user
    settings = get_settings()

    login_resp = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # Request with session cookie
    response = client.get(
        "/api/datasets",
        cookies={settings.session_cookie_name: token},
    )
    assert response.status_code == 200


def test_authenticated_access_via_bearer_header(client: TestClient, test_user) -> None:
    _, username, password = test_user

    login_resp = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    response = client.get(
        "/api/datasets",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


def test_get_current_user_profile_me(client: TestClient, test_user) -> None:
    _, username, password = test_user

    login_resp = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    token = login_resp.json()["access_token"]

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == username
    assert data["is_active"] is True


def test_logout_revokes_session_and_subsequent_request_fails(client: TestClient, test_user) -> None:
    _, username, password = test_user
    settings = get_settings()

    login_resp = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    token = login_resp.json()["access_token"]

    # Logout
    logout_resp = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_resp.status_code == 200
    assert logout_resp.json()["message"] == "Logged out successfully"

    # Subsequent request using that revoked token should fail with 401
    auth_check = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert auth_check.status_code == 401
    assert "revoked" in auth_check.json()["error"]["message"].lower()


def test_expired_session_is_rejected(client: TestClient, test_user, db_session) -> None:
    user, username, _ = test_user
    auth_service = AuthService(db_session)

    # Create an already expired session (-10 seconds)
    session, raw_token = auth_service.create_session(user=user, expire_seconds=-10)

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {raw_token}"},
    )
    assert response.status_code == 401
    assert "expired" in response.json()["error"]["message"].lower()

