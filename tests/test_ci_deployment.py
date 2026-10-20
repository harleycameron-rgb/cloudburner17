import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.error import HTTPError


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "vercel_checks", ROOT / ".github" / "scripts" / "vercel_checks.py"
)
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)


class DeploymentGuardTests(unittest.TestCase):
    def test_only_exact_existing_project_and_source_are_accepted(self):
        project = {
            "id": checks.PROJECT, "accountId": checks.TEAM,
            "name": "waxtabletproject", "rootDirectory": None,
            "link": {"type": "github", "org": "harleycameron-rgb", "repo": "cloudburner17"},
        }
        checks.validate_project(project, "harleycameron-rgb/cloudburner17")
        for key, value in (
            ("id", "other"), ("accountId", "other"), ("name", "cloudburner17"),
            ("rootDirectory", "backend"), ("link", None),
            ("link", {"type": "github", "org": "waxtablet", "repo": "waxtabletproject"}),
        ):
            with self.subTest(key=key), self.assertRaises(ValueError):
                checks.validate_project({**project, key: value}, "harleycameron-rgb/cloudburner17")

    def test_deployment_is_disabled_without_explicit_configuration(self):
        with patch.dict(checks.os.environ, {}, clear=True), \
                patch.object(checks, "build_opener") as network:
            with self.assertRaisesRegex(ValueError, "VERCEL_DEPLOY_ENABLED"):
                checks.verify()
            network.assert_not_called()

    def test_ready_does_not_accept_wrong_project_failed_build_or_wrong_target(self):
        deployment = {"projectId": checks.PROJECT, "readyState": "READY", "target": None}
        checks.validate_ready(deployment, "preview")
        checks.validate_ready({**deployment, "target": "production"}, "production")
        for key, value in (
            ("projectId", "other"), ("readyState", "ERROR"), ("target", "production"),
        ):
            with self.subTest(key=key), self.assertRaises(ValueError):
                checks.validate_ready({**deployment, key: value}, "preview")

    def test_smoke_rejects_arbitrary_hosts_credentials_and_redirects(self):
        for url in (
            "https://example.com", "https://app.vercel.app.evil.test",
            "******app.vercel.app", "http://app.vercel.app",
            "https://app.vercel.app?token=value", "https://app.vercel.app/path",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                checks.validate_base_url(url)
        self.assertIsNone(checks.NoRedirect().redirect_request(None, None, 302, "", {}, ""))
        self.assertEqual(checks.validate_base_url("https://app.vercel.app/"),
                         "https://app.vercel.app")

    def test_protection_is_a_failure_not_a_bypass(self):
        for status in (401, 403):
            with patch.object(checks, "build_opener") as opener:
                opener.return_value.open.side_effect = HTTPError("", status, "", {}, None)
                with self.assertRaisesRegex(ValueError, "Accessibility BLOCKED"):
                    checks.smoke("https://app.vercel.app")

    def test_content_and_security_headers_are_required(self):
        checks.check_response("/runtime", b'{"status":"ok","timestamp":1}',
                              {"Content-Type": "application/json"})
        with self.assertRaises(ValueError):
            checks.check_response("/runtime", b'{"status":"failed"}',
                                  {"Content-Type": "application/json"})
        with self.assertRaises(ValueError):
            checks.check_response("/scandoc", b"SCANDOC SYNTHETIC",
                                  {"Content-Type": "text/html"})
        headers = {"Content-Type": "text/javascript", "X-Content-Type-Options": "nosniff"}
        checks.check_response("/scandoc/app.js",
                              (ROOT / "backend/scandoc/app.js").read_bytes(), headers)
        with self.assertRaises(ValueError):
            checks.check_response("/scandoc/app.js", b"unexpected", headers)
