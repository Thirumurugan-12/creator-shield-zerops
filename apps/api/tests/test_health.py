import os
os.environ.setdefault("DATABASE_URL", "sqlite://")

from fastapi.testclient import TestClient
from apps.api.app.main import app

client = TestClient(app)

def test_health() -> None:
    payload = client.get("/health").json()
    assert payload["status"] == "ok"
    assert payload["storage_backend"] in {"local", "s3"}


def test_proofs_require_authentication() -> None:
    assert client.get("/api/proofs").status_code == 401


def test_demo_session_and_current_user() -> None:
    login = client.post("/api/auth/demo")
    assert login.status_code == 200
    assert login.json()["email"] == "demo@creatorshield.local"
    current = client.get("/api/auth/me")
    assert current.status_code == 200
    assert current.json()["id"] == "demo-creator"
    assert client.get("/api/proofs").status_code == 200


def test_logout_clears_session() -> None:
    client.post("/api/auth/demo")
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401
