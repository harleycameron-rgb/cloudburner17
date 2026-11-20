"""Read-only injected-reader tests: no external network or credentials."""
import unittest

from src.coding_agent_plan import MDLTask
from src.coding_agent_reader import inspect_approved_source

SHA = "a" * 40
REPO = "harleycameron-rgb/cloudburner17"
TASK = MDLTask(REPO, SHA, ("src/agent_core.py",), (), 1)


class ReaderTests(unittest.TestCase):
    def test_pinned_read_and_digest(self):
        calls = []
        def reader(repo, path, sha):
            calls.append((repo, path, sha))
            return b"known source"
        result = inspect_approved_source(TASK, allowlist={REPO: SHA}, read_file=reader)
        self.assertEqual(calls, [(REPO, "src/agent_core.py", SHA)])
        self.assertEqual(result["files"][0]["size_bytes"], 12)
        self.assertEqual(result["writes"], 0)
        self.assertEqual(result["status"], "UNVERIFIED")

    def test_denied_before_reader(self):
        calls = []
        with self.assertRaises(PermissionError):
            inspect_approved_source(TASK, allowlist={}, read_file=lambda *a: calls.append(a))
        self.assertEqual(calls, [])

    def test_no_implicit_reader(self):
        with self.assertRaises(ValueError):
            inspect_approved_source(TASK, allowlist={REPO: SHA}, read_file=None)

    def test_reject_non_bytes_and_oversized(self):
        for value in ("text", b"abcdef"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                inspect_approved_source(TASK, allowlist={REPO: SHA},
                    read_file=lambda *args: value, max_file_bytes=5)

    def test_bound_must_be_integer(self):
        with self.assertRaises(ValueError):
            inspect_approved_source(TASK, allowlist={REPO: SHA},
                read_file=lambda *a: b"x", max_file_bytes=True)


if __name__ == "__main__":
    unittest.main()
