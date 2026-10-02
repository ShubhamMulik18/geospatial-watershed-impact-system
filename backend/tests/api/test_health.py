from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_metadata() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200

    data = response.json()
    assert data["info"]["title"] == "Geospatial Watershed Impact Analysis System"
    assert data["info"]["version"] == "0.1.0"