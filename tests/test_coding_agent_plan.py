"""Offline adversarial checks for the MDL plan-only boundary."""
import unittest

from src.coding_agent_plan import MDLTask, plan_task, status_is_known

SHA = "a" * 40
REPO = "harleycameron-rgb/cloudburner17"
ALLOW = {REPO: SHA}


class PlanTests(unittest.TestCase):
    def task(self, **overrides):
        fields = dict(repository=REPO, base_sha=SHA,
                      permitted_paths=("src/agent_core.py",),
                      checks=("tests/test_zero_data.py",), max_iterations=2)
        fields.update(overrides)
        return MDLTask(**fields)

    def test_deterministic_and_closed(self):
        a = plan_task(self.task(), allowlist=ALLOW)
        self.assertEqual(a, plan_task(self.task(), allowlist=ALLOW))
        self.assertEqual(a["mode"], "PLAN_ONLY")
        self.assertEqual(a["native_gate"], "CLOSED")
        self.assertEqual(a["executed_checks"], [])
        self.assertEqual(len(a["receipt_sha256"]), 64)

    def test_unknown_repository(self):
        with self.assertRaises(PermissionError):
            plan_task(self.task(repository="other/repo"), allowlist=ALLOW)

    def test_stale_revision(self):
        with self.assertRaises(PermissionError):
            plan_task(self.task(base_sha="b" * 40), allowlist=ALLOW)

    def test_bad_paths(self):
        for path in ("../secrets", ".github/workflows/ci.yml", "deploy/prod",
                     "src/../../escape", "src\\escape", "/tmp/file", "src/.env"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                plan_task(self.task(permitted_paths=(path,)), allowlist=ALLOW)

    def test_bad_iterations(self):
        for value in (0, 11, True, "2"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                plan_task(self.task(max_iterations=value), allowlist=ALLOW)

    def test_duplicate_paths(self):
        with self.assertRaises(ValueError):
            plan_task(self.task(permitted_paths=("src/a.py", "src/a.py")), allowlist=ALLOW)

    def test_status_contract(self):
        self.assertTrue(status_is_known("BLOCKED"))
        self.assertFalse(status_is_known("PASSED"))

    def test_no_approval(self):
        with self.assertRaises(PermissionError):
            plan_task(self.task(), allowlist={})


if __name__ == "__main__":
    unittest.main()
