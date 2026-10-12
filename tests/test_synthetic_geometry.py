import contextlib
import importlib
import io
import math
import os
import subprocess
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from modules.synthetic_geometry import GEOMETRY, IN_MEMORY_RESULTS, SyntheticGeometry


class SyntheticGeometryTests(unittest.TestCase):
    def test_default_cycle_is_reproducible_and_in_memory(self):
        geometry = SyntheticGeometry()
        self.assertEqual((geometry.seed, geometry.delta), (1.0, 0.1137))
        self.assertTrue(geometry.in_memory)
        first = geometry.run_cycle()
        self.assertEqual(first, geometry.run_cycle())
        self.assertEqual(first, SyntheticGeometry().run_cycle())
        self.assertEqual(first, IN_MEMORY_RESULTS)
        self.assertTrue(GEOMETRY.in_memory)
        first["func_tap"] = 999
        self.assertNotEqual(first, geometry.run_cycle())
        self.assertEqual(IN_MEMORY_RESULTS, geometry.run_cycle())

    def test_all_eight_scores_match_supplied_formulas_and_seed_order(self):
        coordinates = [
            ("func_tap", lambda s: (math.sin(s), math.cos(s), math.sin(s*0.5))),
            ("func_surface", lambda s: (
                math.sin(s*0.337), math.cos(s*0.771), math.sin(s*0.1137))),
            ("func_gain", lambda s: (
                math.sin(s*0.1137), math.cos(s*0.3371), math.sin(s*0.7711))),
            ("func_habitatat", lambda s: (
                math.sin(s*0.8869), math.cos(s*0.6065), math.sin(s*0.7170))),
            ("func_time", lambda s: (s*0.1137, s*0.3371, s*0.7711)),
            ("func_space", lambda s: (math.sin(s), math.sin(s*2), math.sin(s*3))),
            ("func_scanroot", lambda s: (math.cos(s), math.cos(s*2), math.cos(s*3))),
            ("func_scandoczero", lambda s: (
                math.sin(s*0.1137), math.cos(s*0.3371),
                math.sin(s*0.7711)*math.cos(s*0.8869))),
        ]
        for seed, delta in [(1.0, 0.1137), (-2.0, 0.25), (0.0, 0.0)]:
            with self.subTest(seed=seed, delta=delta):
                geometry = SyntheticGeometry(seed=seed, delta=delta)
                results = geometry.run_cycle()
                self.assertEqual(list(results), [name for name, _ in coordinates])
                s = seed
                for name, fn in coordinates:
                    x, y, z = fn(s)
                    self.assertEqual(results[name], round(abs(x*y*z)*0.1137, 6))
                    self.assertTrue(math.isfinite(results[name]))
                    self.assertGreaterEqual(results[name], 0)
                    s += delta
                self.assertEqual((geometry.seed, geometry.delta), (seed, delta))

    def test_curvature_is_rounded_custom_non_physical_score(self):
        geometry = SyntheticGeometry()
        self.assertEqual(geometry.curvature_score(-1, 2, 3), 0.6822)
        self.assertEqual(geometry.curvature_score(0, 2, 3), 0)
        self.assertEqual(geometry.curvature_score(1, 1, 1/3), 0.0379)

    def test_import_has_no_console_output(self):
        import modules.synthetic_geometry as module

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            importlib.reload(module)
        self.assertEqual(output.getvalue(), "")
        self.assertEqual(module.IN_MEMORY_RESULTS, IN_MEMORY_RESULTS)

    def test_cycle_passes_existing_zero_data_guard(self):
        code = """from modules.synthetic_geometry import SyntheticGeometry, IN_MEMORY_RESULTS
from src.zero_data import install_zero_data_guard, assert_no_file_io
install_zero_data_guard()
geometry = SyntheticGeometry()
assert geometry.in_memory is True
assert geometry.run_cycle() == geometry.run_cycle() == IN_MEMORY_RESULTS
assert len(geometry.run_cycle()) == 8
assert_no_file_io()
"""
        result = subprocess.run(
            [sys.executable, "-B", "-c", code],
            cwd=ROOT_DIR,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
