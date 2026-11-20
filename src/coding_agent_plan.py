"""Fail-closed, deterministic planning boundary for future GitHub coding agents.

No GitHub SDK, network calls, filesystem writes, model inference, or execution.
This module does not authorize code modification or deployment.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Mapping

_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_SHA = re.compile(r"^[0-9a-f]{40}$")
_PATH = re.compile(r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*$")
_STATUSES = frozenset({
    "IMPLEMENTED", "TESTED", "SIMULATED", "UNVERIFIED",
    "NOT IMPLEMENTED", "BLOCKED",
})
_FORBIDDEN = ("deploy", "production", "dns", "visibility", "merge",
              "fire", "ignite", "secret", ".env", "token")


@dataclass(frozen=True)
class MDLTask:
    repository: str
    base_sha: str
    permitted_paths: tuple[str, ...]
    checks: tuple[str, ...]
    max_iterations: int = 1


def _safe_path(value: str) -> bool:
    return (isinstance(value, str) and bool(_PATH.fullmatch(value))
            and not any(part.startswith(".") for part in value.split("/"))
            and not any(term in value.lower() for term in _FORBIDDEN))


def plan_task(task: MDLTask, *, allowlist: Mapping[str, str]) -> dict:
    """Produce a source-pinned proposal without taking any action.

    allowlist maps repository full name to the exact approved 40-character
    base commit SHA. Callers must supply it from a trusted external source.
    """
    if not isinstance(task, MDLTask):
        raise ValueError("MDLTask required")
    if not isinstance(task.repository, str) or not _REPO.fullmatch(task.repository):
        raise ValueError("invalid repository")
    if not isinstance(task.base_sha, str) or not _SHA.fullmatch(task.base_sha):
        raise ValueError("invalid pinned SHA")
    if not isinstance(allowlist, Mapping) or allowlist.get(task.repository) != task.base_sha:
        raise PermissionError("repository or source revision not approved")
    if type(task.max_iterations) is not int or not 1 <= task.max_iterations <= 10:
        raise ValueError("invalid iteration bound")
    if (not isinstance(task.permitted_paths, tuple)
            or not task.permitted_paths
            or len(task.permitted_paths) > 32
            or len(set(task.permitted_paths)) != len(task.permitted_paths)
            or not all(_safe_path(p) for p in task.permitted_paths)):
        raise ValueError("invalid permitted paths")
    if (not isinstance(task.checks, tuple) or len(task.checks) > 16
            or not all(_safe_path(c) for c in task.checks)):
        raise ValueError("invalid checks")
    payload = {
        "schema": "mdl-coding-agent-plan/v1",
        "repository": task.repository,
        "base_sha": task.base_sha,
        "permitted_paths": list(task.permitted_paths),
        "checks": list(task.checks),
        "max_iterations": task.max_iterations,
        "mode": "PLAN_ONLY",
        "status": "UNVERIFIED",
        "native_gate": "CLOSED",
        "proposed_edits": [],
        "executed_checks": [],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["receipt_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return payload


def status_is_known(value: str) -> bool:
    return value in _STATUSES if isinstance(value, str) else False
