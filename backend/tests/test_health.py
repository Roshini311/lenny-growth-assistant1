from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify that the health check endpoint returns HTTP 200 and expected status keys."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "environment" in data
    assert "default_provider" in data
    assert "database" in data
    assert data["database"]["configured"] is True
    assert "providers" in data


def test_root_endpoint():
    """Verify that root endpoint returns API metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["health_url"] == "/api/health"


if __name__ == "__main__":
    test_health_endpoint()
    test_root_endpoint()
    print("[OK] Backend health endpoints verified successfully!")
