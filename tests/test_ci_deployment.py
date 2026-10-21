import importlib.util
from pathlib import Path
import io
import json
import os
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "vercel_checks", ROOT / ".github" / "scripts" / "vercel_checks.py"
)
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)


class DeploymentGuardTests(unittest.TestCase):
    def test_logging_workflows_require_explicit_bash_for_pipefail(self):
        for path in (ROOT / ".github" / "workflows").glob("*.yml"):
            text = path.read_text()
            if "| tee " in text:
                with self.subTest(workflow=path.name):
                    self.assertIn("defaults:\n  run:\n    shell: bash\n", text)

    def test_council_scopes_separate_dispatches_and_keep_superseded_ci_cancellation(self):
        pipeline = (ROOT / ".github/workflows/cloudburner17.yml").read_text()
        council = (ROOT / ".github/workflows/multi-llm-council-tests.yml").read_text()
        compact_pipeline = " ".join(pipeline.split())
        expected_scope_expression = (
            "concurrency_scope: >- ${{ github.event_name == 'workflow_dispatch' "
            "&& format('dispatch-{0}-{1}', inputs.deployment, github.run_id) "
            "|| (github.event.pull_request.number "
            "&& format('pr-{0}', github.event.pull_request.number)) "
            "|| format('ci-{0}', github.ref) }}"
        )
        self.assertIn(expected_scope_expression, compact_pipeline)
        self.assertIn("group: council-tests-${{ inputs.concurrency_scope }}", council)
        self.assertIn("cancel-in-progress: ${{ github.event_name != 'workflow_dispatch' }}",
                      council)

        def scope(event, ref, run_id, deployment=None, pull_number=None):
            if event == "workflow_dispatch":
                return f"council-tests-dispatch-{deployment}-{run_id}"
            if pull_number is not None:
                return f"council-tests-pr-{pull_number}"
            return f"council-tests-ci-{ref}"

        main_ci = scope("push", "refs/heads/main", "100")
        preview = scope("workflow_dispatch", "refs/heads/main", "101", "preview")
        production = scope("workflow_dispatch", "refs/heads/main", "102", "production")
        self.assertNotEqual(main_ci, preview)
        self.assertNotEqual(main_ci, production)
        self.assertNotEqual(preview, production)
        self.assertEqual(main_ci, scope("push", "refs/heads/main", "103"))
        self.assertEqual(scope("pull_request", "refs/pull/9/merge", "104", pull_number=9),
                         scope("pull_request", "refs/pull/9/merge", "105", pull_number=9))

    def test_approved_deployments_share_a_non_cancelling_serial_scope(self):
        workflow = (ROOT / ".github/workflows/vercel-deploy.yml").read_text()
        self.assertIn("group: vercel-approved-deployments", workflow)
        self.assertIn("cancel-in-progress: false", workflow)

    def test_only_exact_existing_project_and_source_are_accepted(self):
        project = {
            "id": checks.PROJECT, "accountId": checks.TEAM,
            "name": checks.PROJECT_NAME, "rootDirectory": checks.PROJECT_ROOT,
            "link": {"type": "github", "org": "harleycameron-rgb", "repo": "cloudburner17"},
        }
        checks.validate_project(project, checks.REPOSITORY)
        for key, value in (
            ("id", "other"), ("accountId", "other"), ("name", "cloudburner17"),
            ("rootDirectory", "."), ("link", None),
            ("link", {"type": "github", "org": "waxtablet", "repo": "waxtabletproject"}),
        ):
            with self.subTest(key=key), self.assertRaises(ValueError):
                checks.validate_project({**project, key: value}, checks.REPOSITORY)

    def test_unresolved_application_surface_blocks_deployment(self):
        with self.assertRaisesRegex(ValueError, "app-surface decision"):
            checks.validate_deployment_surface()

    def test_source_context_fails_closed_when_revision_or_repository_is_wrong_or_missing(self):
        valid = {
            "GITHUB_SHA": "a" * 40,
            "GITHUB_REPOSITORY": checks.REPOSITORY,
            "GITHUB_RUN_ID": "123",
            "GITHUB_RUN_ATTEMPT": "1",
            "DEPLOY_ENVIRONMENT": "preview",
        }
        with patch.dict(os.environ, valid, clear=True):
            self.assertEqual(checks.deployment_context()["source_revision"], "a" * 40)
        for key, value in (
            ("GITHUB_SHA", ""),
            ("GITHUB_SHA", "not-a-commit"),
            ("GITHUB_REPOSITORY", ""),
            ("GITHUB_REPOSITORY", "other/repository"),
        ):
            invalid = {**valid, key: value}
            with self.subTest(key=key, value=value), patch.dict(os.environ, invalid, clear=True):
                with self.assertRaises(ValueError):
                    checks.deployment_context()

    def test_checkout_revision_must_match_workflow_sha_and_git_identity_must_exist(self):
        expected = "a" * 40
        with patch.object(checks.subprocess, "run",
                          return_value=SimpleNamespace(stdout=expected + "\n")):
            checks.validate_checkout_revision(expected)
        with patch.object(checks.subprocess, "run",
                          return_value=SimpleNamespace(stdout="b" * 40)):
            with self.assertRaisesRegex(ValueError, "differs from GITHUB_SHA"):
                checks.validate_checkout_revision(expected)
        with patch.object(checks.subprocess, "run",
                          side_effect=subprocess.CalledProcessError(1, "git")):
            with self.assertRaisesRegex(ValueError, "revision unavailable"):
                checks.validate_checkout_revision(expected)

    def test_deployment_is_disabled_without_explicit_configuration(self):
        with patch.dict(checks.os.environ, {}, clear=True), \
                patch.object(checks, "build_opener") as network:
            with self.assertRaisesRegex(ValueError, "VERCEL_DEPLOY_ENABLED"):
                checks.verify()
            network.assert_not_called()

    def test_unresolved_surface_blocks_preflight_before_vercel_api_even_with_opt_in(self):
        environment = {
            "VERCEL_DEPLOY_ENABLED": "true",
            "VERCEL_GIT_INTEGRATION_DISABLED": "true",
            "VERCEL_PROJECT_ID": checks.PROJECT,
            "VERCEL_ORG_ID": checks.TEAM,
            "VERCEL_TOKEN": "x",
            "GITHUB_SHA": "a" * 40,
            "GITHUB_REPOSITORY": checks.REPOSITORY,
            "GITHUB_RUN_ID": "123",
            "GITHUB_RUN_ATTEMPT": "1",
            "DEPLOY_ENVIRONMENT": "preview",
        }
        with patch.dict(checks.os.environ, environment, clear=True), \
                patch.object(checks, "validate_checkout_revision") as checkout, \
                patch.object(checks, "build_opener") as network:
            with self.assertRaisesRegex(ValueError, "app-surface decision"):
                checks.verify()
            checkout.assert_called_once_with("a" * 40)
            network.assert_not_called()

    def test_ready_does_not_accept_wrong_project_failed_build_or_wrong_target(self):
        identity = {
            "source_revision": "a" * 40,
            "repository": checks.REPOSITORY,
            "run_id": "123",
            "run_attempt": "1",
        }
        deployment = {
            "id": "dpl_immutable123",
            "url": "app.vercel.app",
            "projectId": checks.PROJECT,
            "ownerId": checks.TEAM,
            "readyState": "READY",
            "target": None,
            "meta": {
                "ciSourceRevision": identity["source_revision"],
                "ciRepository": identity["repository"],
                "ciProjectId": checks.PROJECT,
                "ciTeamId": checks.TEAM,
                "ciTarget": "preview",
                "ciWorkflowRunId": identity["run_id"],
                "ciWorkflowRunAttempt": identity["run_attempt"],
            },
        }
        arguments = (
            "preview", identity["source_revision"], identity["repository"],
            identity["run_id"], identity["run_attempt"], "https://app.vercel.app",
            "dpl_immutable123",
        )
        self.assertEqual(
            checks.validate_ready(deployment, *arguments),
            ("dpl_immutable123", "https://app.vercel.app"),
        )
        production = {
            **deployment,
            "target": "production",
            "meta": {**deployment["meta"], "ciTarget": "production"},
        }
        self.assertEqual(
            checks.validate_ready(
                production,
                "production",
                identity["source_revision"],
                identity["repository"],
                identity["run_id"],
                identity["run_attempt"],
                "https://app.vercel.app",
                "dpl_immutable123",
            ),
            ("dpl_immutable123", "https://app.vercel.app"),
        )
        for key, value in (
            ("projectId", "other"),
            ("ownerId", "other"),
            ("readyState", "ERROR"),
            ("target", "production"),
            ("target", "missing"),
            ("id", ""),
            ("id", "other"),
            ("url", "other.vercel.app"),
        ):
            candidate = {**deployment, key: value}
            with self.subTest(key=key), self.assertRaises(ValueError):
                checks.validate_ready(candidate, *arguments)

        for key in ("projectId", "id"):
            with self.subTest(missing=key), self.assertRaises(ValueError):
                checks.validate_ready(
                    {k: v for k, v in deployment.items() if k != key}, *arguments
                )
        with self.assertRaises(ValueError):
            checks.validate_ready({key: value for key, value in deployment.items()
                                   if key != "target"}, *arguments)

    def test_deployment_source_metadata_must_match_checked_out_run(self):
        deployment = {
            "id": "dpl_immutable123",
            "url": "app.vercel.app",
            "projectId": checks.PROJECT,
            "ownerId": checks.TEAM,
            "readyState": "READY",
            "target": None,
            "meta": {
                "ciSourceRevision": "a" * 40,
                "ciRepository": checks.REPOSITORY,
                "ciProjectId": checks.PROJECT,
                "ciTeamId": checks.TEAM,
                "ciTarget": "preview",
                "ciWorkflowRunId": "123",
                "ciWorkflowRunAttempt": "1",
            },
        }
        args = ("preview", "a" * 40, checks.REPOSITORY, "123", "1",
                "https://app.vercel.app", "dpl_immutable123")
        for key, value in (
            ("ciSourceRevision", "b" * 40),
            ("ciRepository", "other/repository"),
            ("ciProjectId", "other"),
            ("ciTeamId", "other"),
            ("ciTarget", "production"),
            ("ciWorkflowRunId", "124"),
        ):
            with self.subTest(key=key), self.assertRaises(ValueError):
                checks.validate_ready(
                    {**deployment, "meta": {**deployment["meta"], key: value}}, *args
                )
        for key in ("ciSourceRevision", "ciRepository", "ciProjectId", "ciTarget"):
            with self.subTest(missing=key), self.assertRaises(ValueError):
                checks.validate_ready(
                    {**deployment, "meta": {k: v for k, v in deployment["meta"].items()
                                            if k != key}}, *args
                )
        for key in ("ciSourceRevision", "ciRepository", "ciTeamId"):
            with self.subTest(missing=key), self.assertRaises(ValueError):
                checks.validate_ready(
                    {**deployment, "meta": {k: v for k, v in deployment["meta"].items()
                                            if k != key}}, *args
                )

    def test_manifest_records_failed_checks_and_only_nonsecret_identity_fields(self):
        context = {
            "GITHUB_SHA": "a" * 40,
            "GITHUB_REPOSITORY": checks.REPOSITORY,
            "GITHUB_RUN_ID": "123",
            "GITHUB_RUN_ATTEMPT": "2",
            "DEPLOY_ENVIRONMENT": "preview",
        }
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, context, clear=True
        ):
            path = Path(directory) / "deployment-verification.json"
            checks.initialize_manifest(path)
            checks.record_manifest_check(path, "preflight", "failed")
            manifest = json.loads(path.read_text())
            self.assertEqual(manifest["schema_version"], 1)
            self.assertEqual(manifest["source_revision"], "a" * 40)
            self.assertEqual(manifest["repository"], checks.REPOSITORY)
            self.assertEqual(manifest["project"]["id"], checks.PROJECT)
            self.assertEqual(manifest["project"]["team_id"], checks.TEAM)
            self.assertEqual(manifest["target"], "preview")
            self.assertEqual(manifest["workflow_run_identity"]["attempt"], "2")
            self.assertEqual(manifest["actual_check_outcomes"]["preflight"], "failed")
            self.assertFalse(manifest["deployment_identity_verified"])
            self.assertIn("not independent authentication", manifest["identity_note"])
            self.assertNotIn("VERCEL_TOKEN", path.read_text())

    def test_ready_rechecks_deployment_id_and_retains_failed_identity(self):
        context = {
            "GITHUB_SHA": "a" * 40,
            "GITHUB_REPOSITORY": checks.REPOSITORY,
            "GITHUB_RUN_ID": "123",
            "GITHUB_RUN_ATTEMPT": "1",
            "DEPLOY_ENVIRONMENT": "preview",
            "VERCEL_TOKEN": "x",
        }
        first = {
            "id": "dpl_expected",
            "url": "app.vercel.app",
            "projectId": checks.PROJECT,
            "ownerId": checks.TEAM,
            "readyState": "READY",
            "target": None,
            "meta": {
                "ciSourceRevision": "a" * 40,
                "ciRepository": checks.REPOSITORY,
                "ciProjectId": checks.PROJECT,
                "ciTeamId": checks.TEAM,
                "ciTarget": "preview",
                "ciWorkflowRunId": "123",
                "ciWorkflowRunAttempt": "1",
            },
        }
        second = {**first, "id": "dpl_wrong"}
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, context, clear=True
        ):
            path = Path(directory) / "deployment-verification.json"
            checks.initialize_manifest(path)
            opener = MagicMock()
            opener.open.side_effect = [
                io.BytesIO(json.dumps(first).encode()),
                io.BytesIO(json.dumps(second).encode()),
            ]
            with patch.object(checks, "build_opener", return_value=opener):
                with self.assertRaisesRegex(ValueError, "Deployment ID changed"):
                    checks.ready("https://app.vercel.app", path)
            self.assertEqual(opener.open.call_count, 2)
            manifest = json.loads(path.read_text())
            self.assertEqual(manifest["deployment_id"], "dpl_wrong")
            self.assertEqual(manifest["immutable_deployment_url"], "https://app.vercel.app")
            self.assertFalse(manifest["deployment_identity_verified"])

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
