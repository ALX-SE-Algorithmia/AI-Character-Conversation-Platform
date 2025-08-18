from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health_ok():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "name" in data
    assert "version" in data
    assert "environment" in data
