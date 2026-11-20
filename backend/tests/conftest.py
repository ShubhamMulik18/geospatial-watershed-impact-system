import uuid
import pytest

from app.core.auth import get_current_user
from app.main import app
from app.models.user import User


@pytest.fixture(autouse=True)
def default_authenticated_user(request):
    """
    Automatically mock authentication for existing tests so that existing test suites
    continue to pass without modification. Tests in `test_auth` or marked with
    `@pytest.mark.no_auth_override` test genuine authentication behavior.
    """
    if "test_auth" in request.node.nodeid or "no_auth_override" in request.keywords:
        yield None
        return

    dummy_user = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        username="test_admin",
        password_hash="mock_hash",
        is_active=True,
    )
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    try:
        yield dummy_user
    finally:
        app.dependency_overrides.pop(get_current_user, None)

