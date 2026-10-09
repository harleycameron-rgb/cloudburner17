"""Offline structural view of the Invariant repository constellation.

No engine imports, network calls, signing, qualification or runtime firing.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re


def canonical_bytes(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def fingerprint(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(whole, local):
    _require(whole.get("schema") == "invariant-whole-topology/1", "whole schema")
    _require(local.get("schema") == "invariant-module-topology/1", "local schema")
    _require(local.get("whole_sha256") == fingerprint(whole), "whole digest mismatch")
    nodes = whole["nodes"]
    ids = [node["id"] for node in nodes]
    _require(len(ids) == len(set(ids)) and bool(ids), "duplicate/empty nodes")
    _require(local["repository"] in ids, "local repository absent")
    centres = whole["centres"]
    _require(len(centres) == len(set(centres)), "duplicate centres")
    _require(set(centres).issubset(ids), "unknown centre")
    for node in nodes:
        _require(re.fullmatch(r"[0-9a-f]{40}", node["source_commit"]), "source commit")
        modules = node["modules"]
        module_ids = [module["id"] for module in modules]
        _require(
            bool(module_ids) and len(module_ids) == len(set(module_ids)),
            "duplicate/empty modules",
        )
        for module in modules:
            path = Path(module["path"])
            _require(
                not path.is_absolute() and ".." not in path.parts and bool(path.parts),
                "unsafe module path",
            )
            _require(re.fullmatch(r"[0-9a-f]{40}", module["git_blob_sha1"]), "source blob digest")
    edges = whole["edges"]
    edge_ids = [(edge["from"], edge["to"], edge["port"]) for edge in edges]
    _require(len(edge_ids) == len(set(edge_ids)), "duplicate edges")
    for edge in edges:
        _require(edge["from"] in ids and edge["to"] in ids, "unknown edge endpoint")
        _require(edge["status"] == "declared", "unverified live connection claim")
        _require(isinstance(edge["port"], str) and bool(edge["port"]), "empty port")
    own = next(node for node in nodes if node["id"] == local["repository"])
    _require(local["role"] == own["role"], "local role mismatch")
    _require(
        local["origin"] == {"signature": None, "bitcoin_anchor": None},
        "this snapshot has no authenticated origin or anchor",
    )
    return own


def load_topology(root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parents[1]
    whole = json.loads((root / "topology" / "whole.json").read_text(encoding="utf-8"))
    local = json.loads((root / "topology" / "module.json").read_text(encoding="utf-8"))
    validate(whole, local)
    return whole, local


def project(whole, local):
    own = validate(whole, local)
    repository = local["repository"]
    return {
        "repository": own["id"],
        "role": own["role"],
        "whole_sha256": fingerprint(whole),
        "centres": whole["centres"],
        "modules": own["modules"],
        "inbound": [edge for edge in whole["edges"] if edge["to"] == repository],
        "outbound": [edge for edge in whole["edges"] if edge["from"] == repository],
        "whole": whole,
        "origin": local["origin"],
        "runtime_connected": False,
    }


def check_sources(whole, local, root):
    own = validate(whole, local)
    root = Path(root).resolve()
    checks = []
    for module in own["modules"]:
        path = (root / module["path"]).resolve()
        actual = None
        if path.is_relative_to(root) and path.is_file():
            content = path.read_bytes()
            header = ("blob " + str(len(content)) + "\0").encode("ascii")
            actual = hashlib.sha1(header + content).hexdigest()
        expected = module["git_blob_sha1"]
        checks.append({
            "module": module["id"],
            "path": module["path"],
            "expected": expected,
            "actual": actual,
            "ok": actual == expected,
        })
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check-sources", action="store_true")
    args = parser.parse_args()
    try:
        whole, local = load_topology(args.root)
        report = project(whole, local)
        if args.check_sources:
            report["source_checks"] = check_sources(whole, local, args.root)
            report["sources_match"] = all(check["ok"] for check in report["source_checks"])
        print(json.dumps(report, indent=2, ensure_ascii=True))
        return 0 if report.get("sources_match", True) else 1
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
