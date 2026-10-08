# ============================================================
# CLOUDBURNER17 — RUNTIME STUB TEST
# ============================================================

from fastapi.testclient import TestClient
from backend.server import app

client = TestClient(app)

def test_runtime_stub():
    response = client.get("/runtime")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
