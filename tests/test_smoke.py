from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app, base_url="http://localhost")

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
