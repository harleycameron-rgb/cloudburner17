from fastapi.testclient import TestClient
from backend.main import app


def test_scandoc_read_only_page_and_allowlisted_assets():
    client = TestClient(app)
    for route in ("/scandoc", "/scandoc/"):
        response = client.get(route)
        assert response.status_code == 200
        assert "SCANDOC" in response.text
        assert "SYNTHETIC" in response.text
        assert "connect-src 'none'" in response.headers["content-security-policy"]
    for asset in ("model.js", "app.js", "style.css"):
        response = client.get("/scandoc/" + asset)
        assert response.status_code == 200
        assert response.headers["x-content-type-options"] == "nosniff"
    assert client.get("/scandoc/main.py").status_code == 404
    assert client.post("/scandoc").status_code == 405
