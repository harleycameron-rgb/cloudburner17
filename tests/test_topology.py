import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("topology_inspector", ROOT / "topology" / "inspect.py")
inspector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inspector)
EXPECTED_DIGEST = "4ff1bbf64b8f1ad2976cf849deac78429a9ce64a69ef1585bd9c73ed9532d9d5"


class TopologyTests(unittest.TestCase):
    def setUp(self):
        self.whole, self.module = inspector.load_topology(ROOT)

    def reject(self, mutate):
        whole, module = copy.deepcopy(self.whole), copy.deepcopy(self.module)
        mutate(whole, module)
        module["whole_sha256"] = inspector.fingerprint(whole)
        with self.assertRaises((ValueError, KeyError, TypeError)):
            inspector.validate(whole, module)

    def test_canonical_commitment(self):
        self.assertEqual(inspector.fingerprint(self.whole), EXPECTED_DIGEST)
        self.assertEqual(inspector.canonical_bytes({"z": "é", "a": 1}), b'{"a":1,"z":"\\u00e9"}')
        with self.assertRaises(ValueError):
            inspector.canonical_bytes({"value": float("nan")})
        with self.assertRaises(ValueError):
            inspector.canonical_bytes({"value": float("inf")})

    def test_projection_is_only_a_declaration(self):
        report = inspector.project(self.whole, self.module)
        self.assertFalse(report["runtime_connected"])
        self.assertEqual(report["origin"], {"signature": None, "bitcoin_anchor": None})
        self.assertEqual(len(report["modules"]), 5)
        self.assertEqual(len(report["inbound"]), 2)
        self.assertEqual(len(report["outbound"]), 2)
        self.assertIs(report["whole"], self.whole)
        self.assertEqual(report["whole_sha256"], EXPECTED_DIGEST)

    def test_schemas_digest_and_local_identity(self):
        for mutation in (
            lambda w, m: w.update(schema="unknown"),
            lambda w, m: m.update(schema="unknown"),
            lambda w, m: m.update(repository="missing"),
            lambda w, m: m.update(role="central-coupler"),
        ):
            with self.subTest(mutation=mutation):
                self.reject(mutation)
        self.module["whole_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "digest"):
            inspector.validate(self.whole, self.module)

    def test_nodes_modules_and_centres(self):
        mutations = (
            lambda w, m: w.update(nodes=[]),
            lambda w, m: w["nodes"].append(copy.deepcopy(w["nodes"][0])),
            lambda w, m: w["nodes"][0].update(id=""),
            lambda w, m: w["nodes"][0].update(source_commit="A" * 40),
            lambda w, m: w["nodes"][0].update(source_commit="0" * 39),
            lambda w, m: w["nodes"][0].update(modules=[]),
            lambda w, m: w["nodes"][0]["modules"].append(copy.deepcopy(w["nodes"][0]["modules"][0])),
            lambda w, m: w["nodes"][0]["modules"][0].update(id=""),
            lambda w, m: w["nodes"][0]["modules"][0].update(git_blob_sha1="G" * 40),
            lambda w, m: w.update(centres=[]),
            lambda w, m: w["centres"].append(w["centres"][0]),
            lambda w, m: w["centres"].append("unknown"),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.reject(mutation)

    def test_unsafe_paths(self):
        for path in ("", " ", ".", "/README.md", "../README.md", "src/../README.md",
                     "src/../../README.md", r"..\README.md", "C:/README.md"):
            with self.subTest(path=path):
                self.reject(lambda w, m: w["nodes"][0]["modules"][0].update(path=path))

    def test_edges_and_unsigned_origin(self):
        mutations = (
            lambda w, m: w["edges"].append(copy.deepcopy(w["edges"][0])),
            lambda w, m: w["edges"][0].update(**{"from": "unknown"}),
            lambda w, m: w["edges"][0].update(to="unknown"),
            lambda w, m: w["edges"][0].update(port=""),
            lambda w, m: w["edges"][0].update(port=5),
            lambda w, m: w["edges"][0].update(status="connected"),
            lambda w, m: m.update(origin={"signature": "signed", "bitcoin_anchor": None}),
            lambda w, m: m.update(origin={"signature": None, "bitcoin_anchor": "confirmed"}),
            lambda w, m: m.update(origin={"signature": None}),
            lambda w, m: m["origin"].update(extra=None),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.reject(mutation)

    def test_source_hashes_use_git_blob_header(self):
        content = b"example\n"
        expected = hashlib.sha1(b"blob 8\0" + content).hexdigest()
        modules = [{"id": "example", "path": "example.txt", "git_blob_sha1": expected}]
        with patch.object(Path, "read_bytes", return_value=content):
            checks = inspector.check_sources(ROOT, modules)
        self.assertEqual(checks[0]["actual"], expected)
        self.assertTrue(checks[0]["ok"])
        with patch.object(Path, "read_bytes", return_value=b"changed"):
            self.assertFalse(inspector.check_sources(ROOT, modules)[0]["ok"])
        with patch.object(Path, "read_bytes", side_effect=FileNotFoundError):
            missing = inspector.check_sources(ROOT, modules)[0]
        self.assertIsNone(missing["actual"])
        self.assertFalse(missing["ok"])

    def test_source_resolution_rejects_symlink_escape(self):
        modules = [{"id": "example", "path": "example.txt", "git_blob_sha1": "0" * 40}]
        with patch.object(Path, "resolve", side_effect=[ROOT, ROOT.parent / "outside"]):
            with self.assertRaisesRegex(ValueError, "escapes"):
                inspector.check_sources(ROOT, modules)

    def test_cli_reports_projection_and_source_mismatch(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(inspector.main(["--root", str(ROOT)]), 0)
        self.assertNotIn("source_checks", json.loads(output.getvalue()))
        checks = [{"ok": False, "actual": None}]
        output = io.StringIO()
        with patch.object(inspector, "check_sources", return_value=checks):
            with contextlib.redirect_stdout(output):
                self.assertEqual(inspector.main(["--root", str(ROOT), "--check-sources"]), 1)
        report = json.loads(output.getvalue())
        self.assertFalse(report["sources_match"])
        self.assertEqual(report["source_checks"], checks)

    def test_cli_successful_source_check(self):
        output = io.StringIO()
        with patch.object(inspector, "check_sources", return_value=[{"ok": True}]):
            with contextlib.redirect_stdout(output):
                self.assertEqual(inspector.main(["--check-sources"]), 0)
        self.assertTrue(json.loads(output.getvalue())["sources_match"])

    def test_cli_errors_are_json(self):
        for error in (ValueError("invalid"), KeyError("schema"), TypeError("bad type"),
                      OSError("unreadable")):
            output = io.StringIO()
            with patch.object(inspector, "load_topology", side_effect=error):
                with contextlib.redirect_stdout(output):
                    self.assertEqual(inspector.main([]), 1)
            report = json.loads(output.getvalue())
            self.assertFalse(report["ok"])
            self.assertTrue(report["error"])


if __name__ == "__main__":
    unittest.main()
