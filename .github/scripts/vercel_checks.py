"""Fail-closed project verification and GET-only smoke checks."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


PROJECT = "prj_NqPa3tWgpxJ5uuZX9OCFnhwHtvd4"
TEAM = "team_FvvGW28W3COeiV8AqQKY3ZA3"
PROJECT_NAME = "waxtabletproject"
PROJECT_ROOT = "backend"
REPOSITORY = "harleycameron-rgb/cloudburner17"
ROOT = Path(__file__).resolve().parents[2]
MANIFEST_CHECKS = (
    "preflight", "cli_install", "vercel_pull", "vercel_build",
    "deployment", "ready", "smoke",
)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_project(project, repository):
    link = project.get("link") or {}
    if (
        project.get("id") != PROJECT
        or project.get("accountId") != TEAM
        or project.get("name") != PROJECT_NAME
        or project.get("rootDirectory") != PROJECT_ROOT
        or link.get("type") != "github"
        or f"{link.get('org')}/{link.get('repo')}" != repository
        or repository != REPOSITORY
    ):
        raise ValueError("Project/team/name/root/Git source mismatch; deployment blocked")


def validate_deployment_surface():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    root_vercel = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    backend_vercel = json.loads(
        (ROOT / "backend" / "vercel.json").read_text(encoding="utf-8")
    )
    entrypoint = project.get("tool", {}).get("vercel", {}).get("entrypoint")
    root_functions = root_vercel.get("functions", {})
    backend_builds = backend_vercel.get("builds", [])
    backend_routes = backend_vercel.get("routes", [])
    if (
        entrypoint != "backend.scandoc_page:app"
        or "backend/main.py" in root_functions
        or any(build.get("src") == "main.py" for build in backend_builds)
        or any("main.py" in route.get("dest", "") for route in backend_routes)
    ):
        raise ValueError(
            "Deployment blocked: owner must resolve the Vercel app-surface decision; "
            "the native backend exposes mutating routes"
        )


def deployment_context():
    revision = os.environ.get("GITHUB_SHA", "")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    run_attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "")
    environment = os.environ.get("DEPLOY_ENVIRONMENT", "")
    if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", revision):
        raise ValueError("GITHUB_SHA missing or invalid; deployment blocked")
    if repository != REPOSITORY:
        raise ValueError("GITHUB_REPOSITORY missing or unapproved; deployment blocked")
    if not run_id.isdecimal() or not run_attempt.isdecimal():
        raise ValueError("Workflow run identity missing or invalid; deployment blocked")
    if environment not in ("preview", "production"):
        raise ValueError("Invalid deployment environment")
    return {
        "source_revision": revision,
        "repository": repository,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "environment": environment,
    }


def validate_checkout_revision(expected_revision):
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        raise ValueError("Checked-out revision unavailable; deployment blocked") from None
    if result.stdout.strip() != expected_revision:
        raise ValueError("Checked-out revision differs from GITHUB_SHA; deployment blocked")


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
    context = deployment_context()
    validate_checkout_revision(context["source_revision"])
    validate_deployment_surface()
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


def validate_ready(deployment, environment, source_revision, repository, run_id, run_attempt,
                   returned_url, expected_deployment_id=None):
    if not isinstance(deployment, dict):
        raise ValueError("Deployment response is invalid; runtime remains unverified")
    expected_target = "production" if environment == "production" else None
    metadata = deployment.get("meta")
    expected_metadata = {
        "ciSourceRevision": source_revision,
        "ciRepository": repository,
        "ciProjectId": PROJECT,
        "ciTeamId": TEAM,
        "ciTarget": environment,
        "ciWorkflowRunId": run_id,
        "ciWorkflowRunAttempt": run_attempt,
    }
    if (
        deployment.get("projectId") != PROJECT
        or deployment.get("ownerId") != TEAM
        or deployment.get("readyState") != "READY"
        or "target" not in deployment
        or deployment.get("target") != expected_target
        or not isinstance(metadata, dict)
        or any(metadata.get(name) != expected for name, expected in expected_metadata.items())
    ):
        raise ValueError(
            "Deployment source/project/team/state/target mismatch; runtime remains unverified"
        )
    deployment_id = deployment.get("id")
    if not isinstance(deployment_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", deployment_id):
        raise ValueError("Deployment ID missing or invalid; runtime remains unverified")
    if expected_deployment_id is not None and deployment_id != expected_deployment_id:
        raise ValueError("Deployment ID changed during identity verification")
    deployment_url = deployment.get("url")
    if not isinstance(deployment_url, str) or not deployment_url:
        raise ValueError("Immutable deployment URL missing; runtime remains unverified")
    immutable_url = validate_base_url("https://" + deployment_url)
    returned = validate_base_url(returned_url)
    if urlsplit(immutable_url).hostname != urlsplit(returned).hostname:
        raise ValueError("Returned deployment URL does not match immutable identity")
    return deployment_id, immutable_url


def _manifest_write(path, manifest):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    temporary.replace(path)


def initialize_manifest(path):
    manifest = {
        "schema_version": 1,
        "source_revision": os.environ.get("GITHUB_SHA") or None,
        "repository": os.environ.get("GITHUB_REPOSITORY") or None,
        "project": {"id": PROJECT, "name": PROJECT_NAME, "team_id": TEAM},
        "deployment_id": None,
        "immutable_deployment_url": None,
        "target": os.environ.get("DEPLOY_ENVIRONMENT") or None,
        "workflow_run_identity": {
            "id": os.environ.get("GITHUB_RUN_ID") or None,
            "attempt": os.environ.get("GITHUB_RUN_ATTEMPT") or None,
        },
        "actual_check_outcomes": {name: "not_run" for name in MANIFEST_CHECKS},
        "observed_deployment_identity": None,
        "deployment_identity_verified": False,
        "identity_note": (
            "Vercel CLI metadata is explicitly supplied and verified as an identity "
            "assertion; it is not independent authentication of the build artifact."
        ),
    }
    _manifest_write(path, manifest)


def record_manifest_check(path, name, outcome):
    if name not in MANIFEST_CHECKS or outcome not in ("passed", "failed"):
        raise ValueError("Invalid deployment manifest check outcome")
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    manifest["actual_check_outcomes"][name] = outcome
    _manifest_write(path, manifest)


def _safe_observation(value):
    return value if isinstance(value, str) and len(value) <= 512 else None


def record_observed_deployment(path, deployment):
    metadata = deployment.get("meta")
    if not isinstance(metadata, dict):
        metadata = {}
    url = deployment.get("url")
    immutable_url = None
    if isinstance(url, str):
        try:
            immutable_url = validate_base_url("https://" + url)
        except ValueError:
            pass
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    manifest["deployment_id"] = _safe_observation(deployment.get("id"))
    manifest["immutable_deployment_url"] = immutable_url
    manifest["observed_deployment_identity"] = {
        "project_id": _safe_observation(deployment.get("projectId")),
        "team_id": _safe_observation(deployment.get("ownerId")),
        "target": _safe_observation(deployment.get("target")),
        "source_revision": _safe_observation(metadata.get("ciSourceRevision")),
        "repository": _safe_observation(metadata.get("ciRepository")),
        "workflow_run_id": _safe_observation(metadata.get("ciWorkflowRunId")),
        "workflow_run_attempt": _safe_observation(metadata.get("ciWorkflowRunAttempt")),
    }
    manifest["deployment_identity_verified"] = False
    _manifest_write(path, manifest)

def ready(base_url, manifest_path=None):
    returned_url = validate_base_url(base_url)
    hostname = urlsplit(returned_url).hostname
    if not hostname.endswith(".vercel.app"):
        raise ValueError("Deployment status requires a Vercel URL")
    context = deployment_context()
    if not os.environ.get("VERCEL_TOKEN"):
        raise ValueError("Deployment status configuration missing")
    request = Request(
        f"https://api.vercel.com/v13/deployments/{hostname}?teamId={TEAM}",
        headers={"Authorization": "Bearer " + os.environ["VERCEL_TOKEN"]},
    )
    with build_opener(NoRedirect).open(request, timeout=20) as response:
        url_lookup = json.load(response)
    deployment_id = url_lookup.get("id") if isinstance(url_lookup, dict) else None
    if not isinstance(deployment_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", deployment_id):
        if manifest_path and isinstance(url_lookup, dict):
            record_observed_deployment(manifest_path, url_lookup)
        raise ValueError("Deployment ID missing or invalid; runtime remains unverified")
    if manifest_path and isinstance(url_lookup, dict):
        record_observed_deployment(manifest_path, url_lookup)
    id_request = Request(
        f"https://api.vercel.com/v13/deployments/{deployment_id}?teamId={TEAM}",
        headers={"Authorization": "Bearer " + os.environ["VERCEL_TOKEN"]},
    )
    with build_opener(NoRedirect).open(id_request, timeout=20) as response:
        deployment = json.load(response)
    if manifest_path:
        record_observed_deployment(manifest_path, deployment)
    deployment_id, immutable_url = validate_ready(
        deployment,
        context["environment"],
        context["source_revision"],
        context["repository"],
        context["run_id"],
        context["run_attempt"],
        returned_url,
        deployment_id,
    )
    if manifest_path:
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        manifest["deployment_id"] = deployment_id
        manifest["immutable_deployment_url"] = immutable_url
        manifest["deployment_identity_verified"] = True
        _manifest_write(manifest_path, manifest)
    print("Deployment READY in intended project/target; accessibility and runtime still unverified")


def validate_base_url(base_url):
    if not isinstance(base_url, str) or any(character.isspace() for character in base_url):
        raise ValueError("Smoke URL must be a bare HTTPS Vercel URL or local loopback")
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
        elif len(sys.argv) == 3 and sys.argv[1] == "manifest-init":
            initialize_manifest(sys.argv[2])
        elif len(sys.argv) == 5 and sys.argv[1] == "manifest-check":
            record_manifest_check(sys.argv[2], sys.argv[3], sys.argv[4])
        elif len(sys.argv) == 3 and sys.argv[1] == "ready":
            ready(sys.argv[2])
        elif len(sys.argv) == 4 and sys.argv[1] == "ready":
            ready(sys.argv[2], sys.argv[3])
        elif len(sys.argv) == 3 and sys.argv[1] == "smoke":
            smoke(sys.argv[2])
        else:
            raise ValueError(
                "Usage: vercel_checks.py verify | ready BASE_URL [MANIFEST] | "
                "smoke BASE_URL | manifest-init PATH | manifest-check PATH NAME STATUS"
            )
    except (ValueError, HTTPError, URLError, TimeoutError) as error:
        # Do not include URLs, response bodies, or authorization data in failures.
        message = str(error) if isinstance(error, ValueError) else "Network/API check failed"
        raise SystemExit(message) from None
