from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_chat_stub():
    r = client.post(
        "/api/v1/chat",
        json={"character_id": "coach", "message": "Hi", "user_id": "u1"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["character_id"] == "coach"
    assert isinstance(data["conversation_id"], str) and len(data["conversation_id"]) > 0
    assert "stub" in data["reply"].lower() or isinstance(data["reply"], str)
