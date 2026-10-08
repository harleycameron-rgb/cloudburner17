import unittest

from src.waxtablet_adapter import WaxtabletAdapter
from src.waxtablet_bridge import waxtablet_bridge


class WaxtabletBridgeTests(unittest.TestCase):
    def test_waxtablet_bridge_routes_a_passing_feed_vector(self):
        result = waxtablet_bridge([
            {"name": "alpha", "ok": True},
            {"name": "beta", "ok": True},
        ])

        self.assertEqual(result["feed"], "ACTIVE")
        self.assertTrue(result["invariantPulse"])
        self.assertEqual(result["ignition"]["residue"], 0)
        self.assertEqual(
            [(entry["name"], entry["ok"]) for entry in result["vector"]],
            [("alpha", True), ("beta", True)],
        )

    def test_waxtablet_bridge_halts_failed_and_empty_vectors(self):
        failed = waxtablet_bridge([{"name": "alpha", "ok": False}])
        empty = waxtablet_bridge([])

        self.assertEqual(failed["feed"], "HALTED")
        self.assertFalse(failed["invariantPulse"])
        self.assertEqual(failed["ignition"]["residue"], 1)
        self.assertEqual(empty["feed"], "HALTED")
        self.assertFalse(empty["invariantPulse"])

    def test_waxtablet_bridge_rejects_invalid_vectors(self):
        for vector in (
            None,
            "alpha",
            [None],
            [{"name": "alpha", "ok": "true"}],
        ):
            with self.subTest(vector=vector), self.assertRaises(TypeError):
                waxtablet_bridge(vector)

    def test_adapter_exposes_the_waxtablet_bridge(self):
        response = WaxtabletAdapter().handle({
            "action": "bridge",
            "vector": [{"name": "alpha", "ok": True}],
        })

        self.assertEqual(response["feed"], "ACTIVE")
        self.assertTrue(response["invariantPulse"])


if __name__ == "__main__":
    unittest.main()
