import os
import subprocess
import sys
import unittest

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, SRC_DIR)

from run_supervised_build import create_supervisor, run_pipeline
from autonomy import self_verify
from harmony import align_modules, smooth_residue, unify_lambdas
from stabiliser import harmonise_state, stabilise_step, verify_sentinel


class ZeroDataPipelineTests(unittest.TestCase):
    def test_pipeline_is_deterministic(self):
        first_results, first_residue = run_pipeline(create_supervisor())
        second_results, second_residue = run_pipeline(create_supervisor())

        self.assertTrue(all(result["status"] == "completed" for result in first_results))
        self.assertEqual(first_results, second_results)
        self.assertEqual(first_residue, second_residue)

    def test_out_of_order_step_is_rejected(self):
        supervisor = create_supervisor()

        result = supervisor.run("ignite", "y")

        self.assertEqual(result["status"], "failed")
        self.assertIn("expected supervised step 'burn'", result["error"])
        self.assertEqual(supervisor.state_log, [])

    def test_persistent_file_writes_are_rejected(self):
        code = """from zero_data import install_zero_data_guard
install_zero_data_guard()
for path, mode in (("/etc/hosts", "r"), ("/tmp/cloudburner17-zero-data-probe", "w")):
    try:
        open(path, mode)
    except PermissionError as error:
        assert "file I/O is disabled" in str(error)
    else:
        raise AssertionError("file I/O was allowed")
"""
        result = subprocess.run(
            [sys.executable, "-B", "-c", code],
            env={**os.environ, "PYTHONPATH": SRC_DIR, "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_stabiliser_and_harmony_contracts(self):
        output = {"InvariantEngine": {"sound": [1], "lambda": [1.0], "times": [0]}}

        self.assertIs(stabilise_step("ignite", output), output)
        self.assertTrue(harmonise_state([("ignite", output, True)]))
        self.assertEqual(align_modules({"ignite": output}), {"ignite": output})
        self.assertEqual(sum(unify_lambdas([2.0, 3.0])), 1.0)
        self.assertEqual(smooth_residue((1.2345678901234, "tag")), (1.234567890123, "tag"))

        with self.assertRaises(ValueError):
            stabilise_step("burn", {"lambda_updated": [float("nan")]})
        with self.assertRaises(ValueError):
            harmonise_state([("residue", (1.0, "tag"), True), ("burn", {"lambda_updated": [1.0]}, True)])

    def test_autonomy_and_sentinel_reproducibility(self):
        self.assertTrue(self_verify())
        _, residue = run_pipeline(create_supervisor())
        self.assertTrue(verify_sentinel(residue["sentinel"]))
        self.assertFalse(verify_sentinel("not-a-sentinel"))


if __name__ == "__main__":
    unittest.main()
