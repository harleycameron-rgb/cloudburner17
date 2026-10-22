import unittest

from src.residue import Residue, typed_residue


class TypedResidueTests(unittest.TestCase):
    def test_groups_residuals_by_kind_and_sorts_models(self):
        result = typed_residue([
            {"model": "model-b", "kind": "semantic", "residual": "claim b"},
            {"model": "model-a", "kind": "syntactic", "residual": "format a"},
            {"model": "model-a", "kind": "semantic", "residual": "claim a"},
            {"model": "model-a", "kind": "epistemic", "residual": ""},
        ])

        self.assertEqual(
            result,
            {
                "syntactic": [
                    {"model": "model-a", "residual": "format a"},
                ],
                "semantic": [
                    {"model": "model-a", "residual": "claim a"},
                    {"model": "model-b", "residual": "claim b"},
                ],
                "epistemic": [
                    {"model": "model-a", "residual": ""},
                ],
            },
        )

    def test_empty_input_returns_all_categories(self):
        self.assertEqual(
            typed_residue([]),
            {"syntactic": [], "semantic": [], "epistemic": []},
        )

    def test_rejects_invalid_shapes_categories_and_duplicates(self):
        with self.assertRaisesRegex(TypeError, "sequence"):
            typed_residue("not a sequence")
        with self.assertRaisesRegex(ValueError, "model, kind, and residual"):
            typed_residue([{"model": "model-a"}])
        with self.assertRaisesRegex(ValueError, "kind must"):
            typed_residue([
                {"model": "model-a", "kind": "other", "residual": "x"},
            ])
        with self.assertRaisesRegex(ValueError, "only one residual"):
            typed_residue([
                {"model": "model-a", "kind": "semantic", "residual": "x"},
                {"model": "model-a", "kind": "semantic", "residual": "y"},
            ])
        with self.assertRaisesRegex(TypeError, "must be a string"):
            typed_residue([
                {"model": "model-a", "kind": "semantic", "residual": 1},
            ])

    def test_legacy_residue_api_is_unchanged(self):
        self.assertEqual(Residue([1, 2], "legacy"), (3.0, "legacy-3"))


if __name__ == "__main__":
    unittest.main()
