"""Source-pinned, read-only GitHub adapter with an injected fetch capability.

The injected reader is supplied by the caller; this module has no credentials,
network client, write API, or implicit fallback to the default branch.
"""
from __future__ import annotations

import hashlib
from typing import Callable, Mapping

from .coding_agent_plan import MDLTask, plan_task


def inspect_approved_source(
    task: MDLTask,
    *,
    allowlist: Mapping[str, str],
    read_file: Callable[[str, str, str], bytes],
    max_file_bytes: int = 262144,
) -> dict:
    """Read approved paths at the exact pinned SHA and return digest evidence.

    read_file(repository, path, sha) must return raw bytes for that exact ref.
    No source contents are persisted or returned. A missing/mismatched reader
    must fail closed; this function cannot independently authenticate GitHub.
    """
    plan = plan_task(task, allowlist=allowlist)
    if not callable(read_file):
        raise ValueError("explicit read_file capability required")
    if type(max_file_bytes) is not int or not 1 <= max_file_bytes <= 1048576:
        raise ValueError("invalid file bound")
    evidence = []
    for path in task.permitted_paths:
        data = read_file(task.repository, path, task.base_sha)
        if not isinstance(data, bytes) or len(data) > max_file_bytes:
            raise ValueError("invalid or oversized source response")
        evidence.append({
            "path": path,
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "source_ref": task.base_sha,
        })
    return {
        "schema": "mdl-source-inspection/v1",
        "plan_receipt_sha256": plan["receipt_sha256"],
        "repository": task.repository,
        "source_sha": task.base_sha,
        "status": "UNVERIFIED",
        "verification_limit": "Reader authenticity and ref enforcement are caller responsibilities",
        "files": evidence,
        "writes": 0,
    }
