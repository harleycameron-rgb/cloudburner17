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
from agent_interface import AgentInterface
from agent_memory import AgentMemory
from agent_validator import AgentValidator
from engine_manifest import ENGINE_MANIFEST
from orchestrator import Orchestrator


class ZeroDataPipelineTests(unittest.TestCase):
    def test_orchestrator_and_benchmark_are_in_memory(self):
        orchestrator = Orchestrator()
        with self.assertRaisesRegex(RuntimeError, "Benchmark data not loaded"):
            orchestrator.run_benchmark()

        orchestrator.load_benchmark_data(
            [{"case": "alpha", "leakage": 0.1}, {"case": "beta", "leakage": 0.25}]
        )
        self.assertEqual(
            orchestrator.run_benchmark()["worst_case_leakage"], 0.25
        )
        result = orchestrator.run_full_engine()
        self.assertEqual(result["agent"]["status"], "complete")
        self.assertEqual(result["benchmark"]["benchmark"], "complete")
        self.assertEqual(result["sentinel"], result["agent"]["sentinel"])

    def test_agent_interface_memory_validator_and_manifest(self):
        interface = AgentInterface()
        self.assertEqual(interface.initialise(), {"status": "initialised"})
        interface.load_benchmark([{"leakage": 0.0}])
        result = interface.run()
        validator = AgentValidator()
        self.assertTrue(validator.validate(result["sentinel"]))
        self.assertTrue(validator.validate(result["sentinel"]))

        memory = AgentMemory()
        self.assertIsNone(memory.pull())
        memory.push({"cycle": 1})
        self.assertEqual(memory.pull(), {"cycle": 1})
        memory.push("transient")
        memory.clear()
        self.assertIsNone(memory.pull())

        self.assertEqual(ENGINE_MANIFEST["mode"], "zero-data")
        self.assertTrue(ENGINE_MANIFEST["invariants"]["no_persistence"])

    def test_benchmark_rejects_invalid_leakage(self):
        orchestrator = Orchestrator()
        orchestrator.load_benchmark_data([{"leakage": float("nan")}])
        with self.assertRaisesRegex(ValueError, "leakage values"):
            orchestrator.run_benchmark()

    def test_00_package_module_entry_points(self):
        environment = {
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        for module in ("stabiliser", "harmony", "autonomy", "agent_core"):
            with self.subTest(module=module):
                result = subprocess.run(
                    [sys.executable, "-m", f"src.{module}"],
                    cwd=os.path.abspath(os.path.join(SRC_DIR, "..")),
                    env=environment,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_agent_executes_supervised_and_autonomous_cycles(self):
        from agent_core import CloudburnerAgent

        agent = CloudburnerAgent()
        result = agent.execute()
        self.assertEqual(result["status"], "complete")
        self.assertEqual(
            [entry[0] for entry in agent.state], ["burn", "ignite", "residue"]
        )
        self.assertTrue(agent.autonomous_mode()["verified"])

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

    def test_00_file_reads_and_writes_are_rejected(self):
        code = """import os
from zero_data import install_zero_data_guard
install_zero_data_guard()
for path, mode in (("/etc/hosts", "r"), ("/tmp/cloudburner17-zero-data-probe", "w")):
    try:
        open(path, mode)
    except PermissionError as error:
        assert "file I/O is disabled" in str(error)
    else:
        raise AssertionError("file I/O was allowed")
try:
    os.listdir("/")
except PermissionError:
    pass
else:
    raise AssertionError("filesystem enumeration was allowed")
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
