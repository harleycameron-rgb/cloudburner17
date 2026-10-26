from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app


def test_tentacle_sphere_is_an_accessible_static_introduction():
    client = TestClient(app)
    for route in ("/tentacle-sphere", "/tentacle-sphere/"):
        response = client.get(route)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert '<html lang="en">' in response.text
        assert 'name="viewport"' in response.text
        assert "<title>Tentacle Sphere" in response.text
        assert "<main>" in response.text
        assert "<h1>Tentacle Sphere</h1>" in response.text
        assert '<a href="/">Return to home</a>' in response.text
        assert '<figure aria-labelledby="visualization-label">' in response.text
        assert 'id="visualization-label">Visualization placeholder' in response.text
        assert "No simulation or live" in response.text
        assert "No visualization is running." in response.text
        assert "max-width: 48rem" in response.text
        assert ":focus-visible" in response.text
        assert "connect-src 'none'" in response.headers["content-security-policy"]
        assert "default-src 'none'" in response.headers["content-security-policy"]
        assert response.headers["x-content-type-options"] == "nosniff"
        for active_content in ("<script", "<form", "<iframe", "<button", "<canvas"):
            assert active_content not in response.text
    assert client.post("/tentacle-sphere").status_code == 405


def test_supervisor_console_remains_available_beside_integrated_home():
    response = TestClient(app).get("/supervisor")
    assert response.status_code == 200
    assert '<a href="/tentacle-sphere">Tentacle Sphere</a>' in response.text
    assert "<h1>CLOUDBURNER17 Supervisor</h1>" in response.text
    for existing_control in (
        "run('burn')", "run('ignite')", "run('residue')",
        'id="admission"', 'id="spherical-scenes"', 'id="spherical-shifts"',
    ):
        assert existing_control in response.text


def test_introduction_does_not_invoke_runtime_or_admission():
    with patch("backend.main.sup") as supervisor, \
            patch("backend.main.evaluate_submission") as admission, \
            patch("backend.main.burn_harness") as burn, \
            patch("backend.main.ignite") as ignite, \
            patch("backend.main.TentacledSphere") as sphere, \
            patch("backend.main.asyncio.create_subprocess_exec") as subprocess:
        assert TestClient(app).get("/tentacle-sphere").status_code == 200
        for action in (supervisor, admission, burn, ignite, sphere, subprocess):
            action.assert_not_called()


def test_existing_api_routes_are_preserved():
    routes = app.openapi()["paths"]
    for path, method in (
        ("/runtime", "GET"),
        ("/tentacled-sphere", "GET"),
        ("/supervise/{step}/{decision}", "POST"),
        ("/admission", "POST"),
        ("/spherical/ignite", "POST"),
    ):
        assert method.lower() in routes[path]
