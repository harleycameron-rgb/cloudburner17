from fastapi.testclient import TestClient
from backend.main import app
from backend.scandoc_page import app as preview_app


def test_scandoc_read_only_page_and_allowlisted_assets():
    client = TestClient(app)
    for route in ("/scandoc", "/scandoc/"):
        response = client.get(route)
        assert response.status_code == 200
        assert "SCANDOC" in response.text
        assert "SYNTHETIC" in response.text
        assert 'id="summary"' in response.text
        assert 'id="geometry-data"' in response.text
        assert 'id="example" disabled' in response.text
        assert "connect-src 'none'" in response.headers["content-security-policy"]
    for asset, media in (("model.js", "text/javascript"),
                         ("app.js", "text/javascript"),
                         ("style.css", "text/css")):
        response = client.get("/scandoc/" + asset)
        assert response.status_code == 200
        assert response.headers["content-type"].split(";")[0] == media
        assert response.headers["x-content-type-options"] == "nosniff"
    assert client.get("/scandoc/main.py").status_code == 404
    assert client.post("/scandoc").status_code == 405


def test_standalone_preview_has_no_lifecycle_routes():
    client = TestClient(preview_app)
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/scandoc"
    assert client.get("/").headers["content-type"].startswith("text/html")
    assert client.get("/scandoc").status_code == 200
    assert client.get("/scandoc/model.js").status_code == 200
    assert client.post("/admission").status_code == 404
    assert client.post("/supervise/burn/y").status_code == 404
    assert client.post("/spherical/ignite").status_code == 404
    assert client.get("/runtime").status_code == 404
    assert client.get("/scandoc/main.py").status_code == 404
    assert client.post("/scandoc").status_code == 405
    assert all(set(methods) <= {"get", "head"}
               for methods in preview_app.openapi()["paths"].values())
