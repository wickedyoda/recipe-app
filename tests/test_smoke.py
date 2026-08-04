from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app, base_url="http://localhost")
