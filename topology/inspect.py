"""Inspect a structural topology commitment without connecting runtimes."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
GIT_SHA1 = re.compile(r"[0-9a-f]{40}")


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


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _sha1(value):
    return isinstance(value, str) and GIT_SHA1.fullmatch(value) is not None


def _relative_path(value):
    return (
        _text(value)
        and "\\" not in value
        and ":" not in value
        and not PurePosixPath(value).is_absolute()
        and ".." not in PurePosixPath(value).parts
        and PurePosixPath(value) != PurePosixPath(".")
    )


def validate(whole, module):
    _require(isinstance(whole, dict), "whole must be an object")
    _require(isinstance(module, dict), "module must be an object")
    _require(whole["schema"] == "invariant-whole-topology/1", "invalid whole schema")
    _require(module["schema"] == "invariant-module-topology/1", "invalid module schema")
    _require(module["whole_sha256"] == fingerprint(whole), "whole digest mismatch")
    nodes = whole["nodes"]
    _require(isinstance(nodes, list) and bool(nodes), "nodes must be a nonempty list")
    node_ids = set()
    local = None
    _require(_text(module["repository"]), "invalid local repository")
    for node in nodes:
        _require(isinstance(node, dict), "node must be an object")
        node_id = node["id"]
        _require(_text(node_id), "invalid node id")
        _require(node_id not in node_ids, "duplicate node id")
        node_ids.add(node_id)
        _require(_text(node["role"]), "invalid node role")
        _require(_sha1(node["source_commit"]), "invalid source commit")
        modules = node["modules"]
        _require(isinstance(modules, list) and bool(modules), "modules must be a nonempty list")
        module_ids = set()
        for item in modules:
            _require(isinstance(item, dict), "module entry must be an object")
            _require(_text(item["id"]), "invalid module id")
            _require(item["id"] not in module_ids, "duplicate module id")
            module_ids.add(item["id"])
            _require(_relative_path(item["path"]), "invalid relative module path")
            _require(_sha1(item["git_blob_sha1"]), "invalid Git blob SHA1")
        if node_id == module["repository"]:
            local = node
    _require(local is not None, "local repository not present")
    _require(module["role"] == local["role"], "local role mismatch")
    centres = whole["centres"]
    _require(isinstance(centres, list) and bool(centres), "centres must be a nonempty list")
    centre_ids = set()
    for centre in centres:
        _require(_text(centre) and centre in node_ids, "unknown centre")
        _require(centre not in centre_ids, "duplicate centre")
        centre_ids.add(centre)
    edges = whole["edges"]
    _require(isinstance(edges, list), "edges must be a list")
    edge_ids = set()
    for edge in edges:
        _require(isinstance(edge, dict), "edge must be an object")
        _require(_text(edge["from"]) and edge["from"] in node_ids, "unknown edge source")
        _require(_text(edge["to"]) and edge["to"] in node_ids, "unknown edge destination")
        _require(_text(edge["port"]), "invalid edge port")
        _require(edge["status"] == "declared", "edge status must be declared")
        key = (edge["from"], edge["to"], edge["port"])
        _require(key not in edge_ids, "duplicate edge")
        edge_ids.add(key)
    _require(
        module["origin"] == {"signature": None, "bitcoin_anchor": None},
        "origin must be unsigned and unanchored",
    )


def load_topology(root=DEFAULT_ROOT):
    root = Path(root)
    whole = json.loads((root / "topology" / "whole.json").read_text(encoding="utf-8"))
    module = json.loads((root / "topology" / "module.json").read_text(encoding="utf-8"))
    validate(whole, module)
    return whole, module


def project(whole, module):
    validate(whole, module)
    repository = module["repository"]
    local = next(node for node in whole["nodes"] if node["id"] == repository)
    return {
        "repository": repository,
        "role": module["role"],
        "whole_sha256": module["whole_sha256"],
        "centres": whole["centres"],
        "modules": local["modules"],
        "inbound": [edge for edge in whole["edges"] if edge["to"] == repository],
        "outbound": [edge for edge in whole["edges"] if edge["from"] == repository],
        "whole": whole,
        "origin": module["origin"],
        "runtime_connected": False,
    }


def check_sources(root, modules):
    root = Path(root).resolve()
    checks = []
    for module in modules:
        _require(_relative_path(module["path"]), "invalid relative module path")
        path = (root / module["path"]).resolve()
        _require(path.is_relative_to(root), "module path escapes repository root")
        actual = None
        try:
            content = path.read_bytes()
        except FileNotFoundError:
            pass
        else:
            header = b"blob " + str(len(content)).encode("ascii") + b"\0"
            actual = hashlib.sha1(header + content).hexdigest()
        expected = module["git_blob_sha1"]
        checks.append({
            "module": module["id"], "path": module["path"],
            "expected": expected, "actual": actual, "ok": actual == expected,
        })
    return checks


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--check-sources", action="store_true")
    args = parser.parse_args(argv)
    try:
        whole, module = load_topology(args.root)
        report = project(whole, module)
        if args.check_sources:
            report["source_checks"] = check_sources(args.root, report["modules"])
            report["sources_match"] = all(check["ok"] for check in report["source_checks"])
        print(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False))
        return 0 if report.get("sources_match", True) else 1
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, indent=2, ensure_ascii=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
