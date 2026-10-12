import json
import math
import os
import sys
import unittest

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, SRC_DIR)

from tentacled_sphere import TentacledSphere


class TentacledSphereTests(unittest.TestCase):
    def test_actuates_all_tentacles_in_declared_order(self):
        sphere = TentacledSphere()

        state = sphere.actuate()

        self.assertEqual(
            list(state),
            [
                "TAP_CONVEX",
                "SURFACE_CONCAVE",
                "GAIN_PSYCHOSOCIAL",
                "HABITATAT_DOMAIN",
                "TIME_CHRONO",
                "SPACE_CHRONO",
                "SCANROOT_LINEAGE",
                "SCANDOCZERO_AUDIT",
            ],
        )
        self.assertEqual(
            [state[name]["label"] for name in state],
            [
                "convex",
                "concave",
                "psychosocial",
                "domain",
                "chrono_time",
                "chrono_space",
                "lineage",
                "audit",
            ],
        )
        self.assertTrue(all(len(item["vector"]) == 3 for item in state.values()))
        self.assertTrue(
            all(math.isfinite(item["curvature"]) and item["curvature"] >= 0
                for item in state.values())
        )
        self.assertTrue(all(math.isfinite(item["timestamp"]) for item in state.values()))

    def test_seed_and_delta_drive_sequential_geometry(self):
        sphere = TentacledSphere(seed=0, delta=1)

        state = sphere.actuate()

        self.assertEqual(state["TAP_CONVEX"]["vector"], [0.0, 1.0, 0.0])
        self.assertEqual(state["SURFACE_CONCAVE"]["vector"], [0.331, 0.717, 0.113])
        self.assertEqual(state["TIME_CHRONO"]["vector"], [0.4548, 1.3484, 3.0844])

    def test_json_export_is_in_memory_and_valid_json(self):
        exported = TentacledSphere().export_json()

        self.assertEqual(list(json.loads(exported)), list(TentacledSphere().tentacles))

    def test_rejects_non_finite_and_non_numeric_inputs(self):
        for seed, delta in ((math.nan, 1), (1, math.inf), (True, 1), (1, "0.1")):
            with self.subTest(seed=seed, delta=delta):
                with self.assertRaises(ValueError):
                    TentacledSphere(seed=seed, delta=delta)

    def test_rejects_values_that_overflow_geometry(self):
        with self.assertRaisesRegex(ValueError, "finite geometry"):
            TentacledSphere(seed=1e308, delta=0).actuate()


if __name__ == "__main__":
    unittest.main()
