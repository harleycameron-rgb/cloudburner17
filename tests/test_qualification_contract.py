"""Offline negative tests; no network, data storage, or live writes."""
import math
import unittest
from research.qualification_contract import FACES, evaluate_faces

class FailClosedPolicyTests(unittest.TestCase):
    def setUp(self):
        self.faces = {
            face: {"semantic_state": "supported", "geometry_ok": True,
                   "provenance_ok": True}
            for face in FACES
        }

    def test_supported_six_is_offline_policy_only(self):
        result = evaluate_faces(self.faces)
        self.assertTrue(result.accepted)
        self.assertEqual(result.authority, "OFFLINE_POLICY_ONLY")
        self.assertEqual(result.live_gate, "CLOSED")
        self.assertFalse(result.sphere_writes)

    def test_missing_sixth_face_rejected(self):
        del self.faces["business"]
        self.assertFalse(evaluate_faces(self.faces, score=1).accepted)

    def test_extra_temporal_arm_rejected(self):
        self.faces["future"] = self.faces["tap"]
        self.assertFalse(evaluate_faces(self.faces).accepted)

    def test_four_states_not_confused(self):
        for state in ("unknown", "disproven", "unsupported"):
            self.faces["tap"]["semantic_state"] = state
            result = evaluate_faces(self.faces, score=1)
            self.assertFalse(result.accepted)
            self.assertIn("tap:" + state, result.reasons)

    def test_score_cannot_override_geometry(self):
        self.faces["engine"]["geometry_ok"] = False
        self.assertFalse(evaluate_faces(self.faces, score=1).accepted)

    def test_score_cannot_override_provenance(self):
        self.faces["surface"]["provenance_ok"] = False
        self.assertFalse(evaluate_faces(self.faces, score=.99).accepted)

    def test_invalid_scores_rejected(self):
        for score in [True, math.inf, math.nan, -1, 2]:
            self.assertFalse(evaluate_faces(self.faces, score=score).accepted)

    def test_invalid_semantic_state_rejected(self):
        self.faces["tap"]["semantic_state"] = "probably"
        self.assertFalse(evaluate_faces(self.faces).accepted)

    def test_predicate_must_be_explicit_true(self):
        self.faces["tap"]["geometry_ok"] = 1
        self.assertFalse(evaluate_faces(self.faces).accepted)

    def test_missing_predicate_rejected(self):
        self.faces["tap"].pop("provenance_ok")
        self.assertFalse(evaluate_faces(self.faces).accepted)

    def test_input_not_mutated(self):
        before = repr(self.faces)
        evaluate_faces(self.faces)
        self.assertEqual(repr(self.faces), before)

    def test_invalid_input_map_rejected(self):
        self.assertFalse(evaluate_faces(None).accepted)

if __name__ == "__main__":
    unittest.main()
