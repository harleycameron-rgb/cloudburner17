import asyncio
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import urljoin

from fastapi.testclient import TestClient
import pytest

from backend.main import app
from backend.live_feedback_page import app as preview_app


ROOT = Path(__file__).resolve().parents[2]


def test_live_feedback_page_and_module_paths():
    for target in (app, preview_app):
        client = TestClient(target)
        for route in ("/live-feedback", "/live-feedback/"):
            response = client.get(route)
            assert response.status_code == 200
            assert "Manual research inputs" in response.text
            assert "not app telemetry" in response.text
            assert 'src="/live-feedback/live.mjs"' in response.text
            assert "connect-src 'none'" in response.headers["content-security-policy"]
            assert response.headers["permissions-policy"] == "camera=(self), microphone=(self)"
            script = urljoin(route, "/live-feedback/live.mjs")
            assert client.get(script).status_code == 200
            assert client.get(urljoin(script, "./model.mjs")).status_code == 200
        for asset in ("live.mjs", "model.mjs"):
            response = client.get("/live-feedback/" + asset)
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/javascript")
            assert response.headers["x-content-type-options"] == "nosniff"
        for asset in ("main.py", "model.test.mjs", "index.html", "unknown.mjs"):
            assert client.get("/live-feedback/" + asset).status_code == 404
        assert client.post("/live-feedback").status_code == 405


def test_discoverable_link_and_isolated_preview_routes():
    client = TestClient(app)
    assert 'href="/live-feedback"' in client.get("/").text
    assert 'href="/live-feedback"' in (ROOT / "frontend/index.html").read_text()
    client = TestClient(preview_app)
    for route in ("/supervise/burn/y", "/supervise/ignite/y", "/spherical/ignite", "/admission"):
        assert client.post(route, json={}).status_code == 404


def test_assets_are_served_without_filesystem_access():
    # The audit hook is irreversible: exercise lifespan in a disposable process.
    code = """
import asyncio
from backend.main import app, lifespan
from backend.live_feedback_page import live_feedback, live_feedback_asset
from backend.scandoc_page import scandoc
from zero_data import assert_no_file_io

async def request(path):
    messages = []
    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}
    async def send(message):
        messages.append(message)
    await app({
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
        "method": "GET", "scheme": "http", "path": path, "raw_path": path.encode(),
        "query_string": b"", "root_path": "", "headers": [],
        "client": ("127.0.0.1", 1234), "server": ("127.0.0.1", 8000),
    }, receive, send)
    assert messages[0]["status"] == 200, messages
    return b"".join(message.get("body", b"") for message in messages)

async def check():
    async with lifespan(app):
        assert b'href="/live-feedback"' in await request("/")
        for path in ("/live-feedback", "/live-feedback/", "/live-feedback/live.mjs",
                     "/live-feedback/model.mjs", "/runtime", "/scandoc"):
            await request(path)
        assert (await live_feedback()).status_code == 200
        assert (await live_feedback_asset("live.mjs")).media_type == "text/javascript"
        assert (await live_feedback_asset("model.mjs")).status_code == 200
        assert (await scandoc()).status_code == 200
        assert_no_file_io()

asyncio.run(check())
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", code], cwd=ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("module", ["backend.main", "main"])
def test_vercel_source_archive_imports_main_from_any_working_directory(tmp_path, module):
    config = json.loads((ROOT / "vercel.json").read_text())
    build = next(item for item in config["builds"] if item["src"] == "backend/main.py")
    # Expand the explicit brace glob, preserving the repository layout in an
    # isolated archive. This is a source-inclusion check, not a Vercel deployment.
    patterns = build["config"]["includeFiles"].strip("{}").split(",")
    included = {ROOT / build["src"], ROOT / "backend/requirements.txt"}
    for pattern in patterns:
        if pattern.endswith("/**"):
            pattern += "/*"
        included.update(path for path in ROOT.glob(pattern) if path.is_file())
    assert ROOT / "src/admission.py" in included
    assert ROOT / "src/spherical_runtime_bridge.mjs" in included
    assert ROOT / "src/spherical_topology.js" in included
    assert ROOT / "package.json" in included
    for path in included:
        target = tmp_path / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    code = f"""
import importlib
from pathlib import Path
from fastapi.testclient import TestClient
module = importlib.import_module({module!r})
import admission
assert Path(admission.__file__).resolve().is_relative_to(Path({str(tmp_path)!r}))
client = TestClient(module.app)
assert client.get("/runtime").status_code == 200
assert client.get("/").status_code == 200
assert client.get("/scandoc").status_code == 200
assert client.get("/live-feedback").status_code == 200
assert client.get("/live-feedback/model.mjs").status_code == 200
"""
    cwd = tmp_path if module == "backend.main" else tmp_path / "backend"
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-B", "-c", code], cwd=cwd, env=env,
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_vercel_routes_preserve_previews_and_backend_fallback():
    config = json.loads((ROOT / "vercel.json").read_text())
    for route, destination in (
        ("/live-feedback", "/backend/live_feedback_page.py"),
        ("/live-feedback/live.mjs", "/backend/live_feedback_page.py"),
        ("/scandoc/model.js", "/backend/scandoc_page.py"),
        ("/", "/backend/main.py"),
        ("/runtime", "/backend/main.py"),
        ("/admission", "/backend/main.py"),
        ("/spherical/ignite", "/backend/main.py"),
    ):
        match = next(item for item in config["routes"] if re.fullmatch(item["src"], route))
        assert match["dest"] == destination
    for build in config["builds"]:
        assert (ROOT / build["src"]).is_file()
