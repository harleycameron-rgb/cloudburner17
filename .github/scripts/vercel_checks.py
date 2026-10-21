"""Fail-closed project verification and GET-only smoke checks."""

import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


PROJECT = "prj_NqPa3tWgpxJ5uuZX9OCFnhwHtvd4"
TEAM = "team_FvvGW28W3COeiV8AqQKY3ZA3"
ROOT = Path(__file__).resolve().parents[2]


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_project(project, repository):
    link = project.get("link") or {}
    if (
        project.get("id") != PROJECT
        or project.get("accountId") != TEAM
        or project.get("name") != "waxtabletproject"
        or project.get("rootDirectory") not in (None, "", ".")
        or link.get("type") != "github"
        or f"{link.get('org')}/{link.get('repo')}" != repository
        or repository != "harleycameron-rgb/cloudburner17"
    ):
        raise ValueError("Project/team/name/root/Git source mismatch; deployment blocked")


def verify():
    required = {
        "VERCEL_DEPLOY_ENABLED": "true",
        "VERCEL_GIT_INTEGRATION_DISABLED": "true",
        "VERCEL_PROJECT_ID": PROJECT,
        "VERCEL_ORG_ID": TEAM,
    }
    for name, expected in required.items():
        if os.environ.get(name) != expected:
            raise ValueError(f"{name} missing or unapproved; deployment blocked")
    if os.environ.get("DEPLOY_ENVIRONMENT") not in ("preview", "production"):
        raise ValueError("Invalid deployment environment")
    if not os.environ.get("VERCEL_TOKEN"):
        raise ValueError("VERCEL_TOKEN missing; deployment blocked")
    request = Request(
        f"https://api.vercel.com/v9/projects/{PROJECT}?teamId={TEAM}",
        headers={"Authorization": "Bearer " + os.environ["VERCEL_TOKEN"]},
    )
    with build_opener(NoRedirect).open(request, timeout=20) as response:
        project = json.load(response)
    validate_project(project, os.environ.get("GITHUB_REPOSITORY"))
    print("Verified existing project mapping; no project was created")


def validate_ready(deployment, environment):
    if (
        deployment.get("projectId") != PROJECT
        or deployment.get("readyState") != "READY"
        or deployment.get("target") != ("production" if environment == "production" else None)
    ):
        raise ValueError("Deployment project/state/target mismatch; runtime remains unverified")


def ready(base_url):
    hostname = urlsplit(validate_base_url(base_url)).hostname
    if not hostname.endswith(".vercel.app"):
        raise ValueError("Deployment status requires a Vercel URL")
    environment = os.environ.get("DEPLOY_ENVIRONMENT")
    if environment not in ("preview", "production") or not os.environ.get("VERCEL_TOKEN"):
        raise ValueError("Deployment status configuration missing")
    request = Request(
        f"https://api.vercel.com/v13/deployments/{hostname}?teamId={TEAM}",
        headers={"Authorization": "Bearer " + os.environ["VERCEL_TOKEN"]},
    )
    with build_opener(NoRedirect).open(request, timeout=20) as response:
        validate_ready(json.load(response), environment)
    print("Deployment READY in intended project/target; accessibility and runtime still unverified")


def validate_base_url(base_url):
    parsed = urlsplit(base_url)
    loopback = parsed.hostname == "127.0.0.1" and parsed.scheme == "http"
    remote = (
        parsed.scheme == "https"
        and parsed.hostname is not None
        and parsed.hostname.endswith(".vercel.app")
        and parsed.port in (None, 443)
    )
    if (
        not (loopback or remote)
        or parsed.username or parsed.password or parsed.query or parsed.fragment
        or parsed.path not in ("", "/")
    ):
        raise ValueError("Smoke URL must be a bare HTTPS Vercel URL or local loopback")
    return base_url.rstrip("/")


def check_response(route, body, headers):
    media = headers.get("Content-Type", "").split(";")[0]
    if route == "/runtime":
        data = json.loads(body)
        if media != "application/json" or data.get("status") != "ok":
            raise ValueError("Runtime status contract failed")
        if not isinstance(data.get("timestamp"), (int, float)):
            raise ValueError("Runtime timestamp missing")
    elif route == "/":
        if media != "text/html" or b"CLOUDBURNER17 Supervisor" not in body:
            raise ValueError("Unexpected main application")
    elif route == "/scandoc":
        if (
            media != "text/html" or b"SCANDOC" not in body or b"SYNTHETIC" not in body
            or "connect-src 'none'" not in headers.get("Content-Security-Policy", "")
        ):
            raise ValueError("SCANDOC page or containment header mismatch")
    else:
        asset = route.removeprefix("/scandoc/")
        expected_media = {"app.js": "text/javascript", "model.js": "text/javascript",
                          "style.css": "text/css"}
        if (
            asset not in expected_media or media != expected_media[asset]
            or headers.get("X-Content-Type-Options") != "nosniff"
            or body != (ROOT / "backend" / "scandoc" / asset).read_bytes()
        ):
            raise ValueError("Static asset differs from tested source or headers")


def smoke(base_url):
    base_url = validate_base_url(base_url)
    opener = build_opener(NoRedirect)
    for route in ("/", "/runtime", "/scandoc", "/scandoc/app.js",
                  "/scandoc/model.js", "/scandoc/style.css"):
        try:
            with opener.open(base_url + route, timeout=20) as response:
                if response.status != 200:
                    raise ValueError("Expected HTTP 200")
                check_response(route, response.read(2 * 1024 * 1024), response.headers)
        except HTTPError as error:
            if error.code in (401, 403):
                raise ValueError(
                    "Accessibility BLOCKED by authentication; READY is not a public/runtime pass"
                ) from None
            raise ValueError(f"GET {route}: HTTP {error.code}; no redirects followed") from None
        print(f"GET {route}: 200; content contract passed")
    print("Read-only accessibility and selected runtime checks passed; no live qualification")


if __name__ == "__main__":
    try:
        if sys.argv[1:] == ["verify"]:
            verify()
        elif len(sys.argv) == 3 and sys.argv[1] == "ready":
            ready(sys.argv[2])
        elif len(sys.argv) == 3 and sys.argv[1] == "smoke":
            smoke(sys.argv[2])
        else:
            raise ValueError("Usage: vercel_checks.py verify | ready BASE_URL | smoke BASE_URL")
    except (ValueError, HTTPError, URLError, TimeoutError) as error:
        # Do not include URLs, response bodies, or authorization data in failures.
        message = str(error) if isinstance(error, ValueError) else "Network/API check failed"
        raise SystemExit(message) from None
