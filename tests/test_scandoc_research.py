import copy
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from research.scandoc.benchmark import (
    adapt_recorded, canonical, claim_gate, commitment, fit_training,
    geometry_controls, recovery_control, replay, run, semantic_control,
)
from research.scandoc.fixtures import CONTRACT, SEMANTIC

ROOT = Path(__file__).resolve().parents[1]
REVISION = "cb6372d58de35c23d9460f467bbb6e954dd57e99"


class SemanticControlsTests(unittest.TestCase):
    def test_generic_compression_increases_overlap_but_discards_distinctions(self):
        responses = SEMANTIC["forced-generic-compression"]
        identity = semantic_control(responses, "identity")
        coarse = semantic_control(responses, "coarse")
        self.assertEqual(identity["overlap_jaccard"], 0)
        self.assertEqual(coarse["overlap_jaccard"], 1)
        self.assertEqual(coarse["retention_fraction"], 0)
        self.assertEqual(coarse["discarded_information"], ["cause:a", "effect:b"])
        self.assertEqual(identity["retention_fraction"], 1)

    def test_shared_core_and_bijective_variant(self):
        raw = SEMANTIC["shared-core"]
        a = semantic_control(raw, "identity")
        b = semantic_control(raw, "distinction-preserving")
        self.assertEqual(a["overlap_jaccard"], 1 / 3)
        self.assertEqual(a["overlap_jaccard"], b["overlap_jaccard"])
        self.assertEqual(b["retention_fraction"], 1)
        self.assertEqual(b["discarded_information"], [])

    def test_persistent_disagreement_visible_even_when_representation_hides_it(self):
        for variant in CONTRACT["semantic"]["representations"]:
            result = semantic_control(SEMANTIC["persistent-disagreement"], variant)
            self.assertTrue(result["contradiction"]["present_in_input"])
            self.assertEqual(result["contradiction"]["positive_responses"], [0])
            self.assertEqual(result["contradiction"]["negative_responses"], [1])
            self.assertEqual(result["contradiction"]["visible_in_representation"],
                             variant != "coarse")
            self.assertEqual(result["raw_annotations"], SEMANTIC["persistent-disagreement"])

    def test_recorded_adapter_does_not_verify_prose_or_discard_failures(self):
        data = {"rounds": [{"replies": [
            {"model": "a", "content": "A plausible claim."},
            {"model": "b", "content": "[ERROR] unavailable"},
            {"model": "c", "content": ""},
        ]}]}
        annotations = [["claim:p"], ["claim:not-p"], ["unknown"]]
        result = adapt_recorded(data, annotations)
        self.assertEqual([o["status"] for o in result["observations"]],
                         ["unverified", "failed", "missing"])
        self.assertEqual(result["claim"]["status"], "unresolved")
        self.assertEqual(result["observations"][0]["raw"], data["rounds"][0]["replies"][0])
        self.assertEqual(adapt_recorded(data, annotations, "external")[
            "observations"][0]["origin"], "external")
        with self.assertRaises(ValueError):
            adapt_recorded(data, annotations[:2])

    def test_invalid_semantic_inputs(self):
        for responses in ([], [["ok"]], [["ok"], []], [["secret text"], ["ok"]],
                          [["x"]] * 33, [["x" * 81], ["ok"]]):
            with self.subTest(responses=responses), self.assertRaises(ValueError):
                semantic_control(responses, "identity")
        with self.assertRaises(ValueError):
            semantic_control([["x"], ["y"]], "unknown")


class GeometryControlsTests(unittest.TestCase):
    def setUp(self):
        self.raw = run(REVISION)["content"]["geometry"]["raw_inputs"]

    def test_rotation_and_frame_preserve_all_declared_distances(self):
        result = geometry_controls(self.raw)
        for name in ("rotation", "coordinate-frame"):
            control = result["controls"][name]
            self.assertEqual(control["status"], "invariant-preserved")
            self.assertLessEqual(control["max_pair_distance_error"], 1e-10)
            for residue in control["residue"]:
                self.assertLess(residue["reconstruction_error"], 1e-12)
                self.assertAlmostEqual(sum(a * b for a, b in zip(
                    residue["normal_vector"], residue["tangent_vector"])), 0, places=12)

    def test_deformation_detected_and_raw_input_preserved(self):
        before = copy.deepcopy(self.raw)
        result = geometry_controls(self.raw)
        self.assertEqual(result["controls"]["single-arm-deformation"]["status"], "falsified")
        self.assertGreater(result["controls"]["single-arm-deformation"]["max_pair_distance_error"], .01)
        self.assertEqual(result["raw_inputs"], before)
        self.assertEqual(self.raw, before)

    def test_shuffled_time_retains_spatial_but_changes_temporal_metric(self):
        shuffled = geometry_controls(self.raw)["controls"]["shuffled-time"]
        self.assertEqual(shuffled["max_pair_distance_error"], 0)
        self.assertGreater(abs(shuffled["path_length_change"]), .01)
        self.assertEqual(shuffled["temporal_order"], [2, 0, 3, 1])

    def test_unsupported_cannot_pass_and_zero_normal_is_explicit(self):
        result = geometry_controls(self.raw)
        for name in ("boundary-removal", "boundary-replacement", "tap-surface"):
            self.assertEqual(result[name]["status"], "unsupported")
            self.assertIn("reason", result[name])
        short = geometry_controls([[[0, 0, 0]], [[1, 0, 0]]])
        self.assertTrue(all(c["status"] == "unsupported" for c in short["controls"].values()))
        zero = geometry_controls([[[0, 0, 0], [1, 0, 0]]] * 2)
        self.assertEqual(zero["controls"]["rotation"]["residue"][0]["status"], "unsupported")

    def test_invalid_and_nonfinite_rejected(self):
        for bad in (math.nan, math.inf, -math.inf, True, "1", 1e7):
            raw = copy.deepcopy(self.raw)
            raw[0][0][0] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                geometry_controls(raw)
        for bad in ([], self.raw[:1], [[], []], [[[1, 2]], [[1, 2]]]):
            with self.assertRaises(ValueError):
                geometry_controls(bad)


class RecoveryAndEvidenceTests(unittest.TestCase):
    def test_holdout_cannot_change_fit_or_calibration(self):
        policy = CONTRACT["recovery"]
        first = recovery_control(policy["training"], policy["held_out"], policy["perturbation"])
        adversarial = recovery_control(policy["training"], [[999, -999, 50]],
                                       policy["perturbation"])
        self.assertEqual(first["model"], adversarial["model"])
        self.assertEqual(first["model"], fit_training(policy["training"]))
        self.assertEqual(first["model"]["noise_floor_training_only"], .02)
        self.assertNotEqual(first["trials"], adversarial["trials"])

    def test_bounded_operator_recovery_matches_declared_contraction(self):
        policy = CONTRACT["recovery"]
        result = recovery_control(policy["training"], policy["held_out"], [0.1, 0, 0])
        self.assertEqual(result["operator"], policy["operator"])
        for trial in result["trials"]:
            errors = trial["paired_perturbation_errors"]
            self.assertEqual(len(errors), 13)
            for tick, error in enumerate(errors):
                self.assertAlmostEqual(error, .1 * .675 ** tick, places=12)
        with self.assertRaises(ValueError):
            recovery_control(policy["training"], policy["held_out"], [.3, 0, 0])

    def test_claims_fail_closed(self):
        self.assertEqual(claim_gate([])["status"], "unresolved")
        for status in ("failed", "missing", "unverified", "unsupported", "passed", None):
            self.assertEqual(claim_gate([{"status": status}])["status"], "unresolved")
        for item in ({"status": "verified"}, {"status": "verified", "origin": "external",
                     "check": True}, {"status": "verified", "origin": "synthetic", "check": 1}):
            self.assertEqual(claim_gate([item])["status"], "unresolved")
        self.assertEqual(run(REVISION)["content"]["research_claim"]["status"], "unresolved")

    def test_deterministic_commitment_and_replay(self):
        a = run(REVISION)
        with patch("src.tentacled_sphere.time.time", return_value=999):
            b = run(REVISION)
        self.assertEqual(a, b)
        self.assertEqual(replay(a)["status"], "verified")
        independently_hashed = hashlib.sha512(json.dumps(
            a["content"], sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False).encode()).hexdigest()
        self.assertEqual(independently_hashed, a["content_commitment"])
        self.assertEqual(commitment(a["content"]["geometry"]), a["geometry_commitment"])
        b["event"] = {"exported_at": "arbitrary local event, not attestation"}
        self.assertEqual(replay(b)["status"], "verified")
        self.assertEqual(a["content_commitment"], b["content_commitment"])

    def test_forged_success_rejected_even_with_recomputed_hash(self):
        for section in ("research_claim", "geometry", "configuration"):
            evidence = run(REVISION)
            evidence["content"][section] = {"status": "success"}
            evidence["content_commitment"] = commitment(evidence["content"])
            evidence["geometry_commitment"] = commitment(evidence["content"]["geometry"])
            self.assertEqual(replay(evidence)["status"], "rejected")
        self.assertEqual(replay({})["status"], "rejected")
        evidence = run(REVISION)
        evidence["content"]["recovery"]["trials"][0]["paired_perturbation_errors"][0] = 999
        self.assertEqual(replay(evidence)["status"], "rejected")
        with self.assertRaises(ValueError):
            run("not-a-revision")

    def test_import_and_run_under_zero_data_guard_without_network(self):
        code = """import socket
from unittest.mock import patch
from research.scandoc.benchmark import run, replay
from src.zero_data import install_zero_data_guard, assert_no_file_io
install_zero_data_guard()
with patch.object(socket.socket, 'connect', side_effect=AssertionError('offline')):
    assert replay(run('%s'))['status'] == 'verified'
assert_no_file_io()
""" % REVISION
        result = subprocess.run(
            [sys.executable, "-B", "-c", code], cwd=ROOT,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_export_does_not_bypass_installed_persistence_guard(self):
        code = """import sys
from research.scandoc.__main__ import main
from src.zero_data import install_zero_data_guard
install_zero_data_guard()
sys.argv = ['scandoc', 'export', '--revision', '%s', '--output', '/tmp/forbidden-scandoc.json']
try:
    main()
except PermissionError:
    pass
else:
    raise AssertionError('export bypassed runtime guard')
""" % REVISION
        result = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_explicit_export_replay_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "evidence.json"
            base = [sys.executable, "-B", "-m", "research.scandoc"]
            command = base + ["export", "--revision", REVISION, "--output", str(output)]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            evidence = json.loads(output.read_text())
            self.assertEqual(replay(evidence)["status"], "verified")
            self.assertNotIn("raw", evidence["content"])
            verified = subprocess.run(base + ["replay", str(output)], cwd=ROOT,
                                      capture_output=True, text=True)
            self.assertEqual(verified.returncode, 0, verified.stderr)
            self.assertEqual(json.loads(verified.stdout)["status"], "verified")
            before = output.read_bytes()
            again = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(again.returncode, 0)
            self.assertEqual(output.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
