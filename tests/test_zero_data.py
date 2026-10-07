import os
import sys
import unittest

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, SRC_DIR)

from run_supervised_build import create_supervisor, run_pipeline
from zero_data import install_zero_data_guard


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
        install_zero_data_guard()
        path = os.path.join("/tmp", f"cloudburner17-zero-data-{os.getpid()}")

        with self.assertRaisesRegex(PermissionError, "persistent file I/O is disabled"):
            open(path, "w")


if __name__ == "__main__":
    unittest.main()
