from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app, base_url="http://localhost")

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_tailnet_proxy_host_is_accepted():
    r = client.get("/health", headers={"Host": "recipes.example.ts.net"})
    assert r.status_code == 200


def test_login_email_is_case_insensitive():
    r = client.post(
        "/auth/login",
        headers={"Host": "recipes.example.ts.net"},
        json={"email": "ADMIN@EXAMPLE.COM", "password": "ChangeMe123!"},
    )
    assert r.status_code == 200
    assert r.json()["user"]["email"] == "admin@example.com"
