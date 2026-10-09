#!/usr/bin/env python3
"""Add owner-write permission to repositories listed in repo_manifest.json."""

import argparse
import json
import os
import stat
import sys
from pathlib import Path


MANIFEST_PATH = Path(__file__).with_name("repo_manifest.json")


def load_repositories(manifest_path):
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read manifest {manifest_path}: {error}") from error

    repositories = manifest.get("repositories") if isinstance(manifest, dict) else None
    if not isinstance(repositories, list):
        raise ValueError("manifest must contain a 'repositories' array")

    targets = []
    seen = set()
    for index, item in enumerate(repositories):
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise ValueError(f"repositories[{index}] must contain a string 'path'")

        raw_path = Path(item["path"]).expanduser()
        candidate = raw_path if raw_path.is_absolute() else manifest_path.parent / raw_path
        if candidate.is_symlink():
            raise ValueError(f"repositories[{index}] is a symlink: {candidate}")
        try:
            target = candidate.resolve(strict=True)
        except OSError as error:
            raise ValueError(f"repositories[{index}] does not exist: {candidate}") from error
        if not target.is_dir():
            raise ValueError(f"repositories[{index}] is not a directory: {target}")
        if target == Path(target.anchor):
            raise ValueError(f"refusing filesystem root as a repository: {target}")
        if target in seen:
            raise ValueError(f"duplicate repository path: {target}")

        seen.add(target)
        targets.append(target)
    return targets


def collect_changes(targets):
    changes = []
    errors = []

    def visit(path):
        try:
            metadata = path.lstat()
        except OSError as error:
            errors.append(f"{path}: {error}")
            return

        if stat.S_ISLNK(metadata.st_mode):
            return
        if not (stat.S_ISDIR(metadata.st_mode) or stat.S_ISREG(metadata.st_mode)):
            return

        old_mode = stat.S_IMODE(metadata.st_mode)
        new_mode = old_mode | stat.S_IWUSR
        if new_mode != old_mode:
            changes.append((path, old_mode, new_mode))

        if stat.S_ISDIR(metadata.st_mode):
            try:
                with os.scandir(path) as entries:
                    children = sorted((Path(entry.path) for entry in entries), key=str)
            except OSError as error:
                errors.append(f"{path}: {error}")
                return
            for child in children:
                visit(child)

    for target in targets:
        visit(target)
    return changes, errors


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Add owner-write permission to manifest repositories, recursively."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=MANIFEST_PATH,
        help=f"JSON manifest path (default: {MANIFEST_PATH})",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="apply changes; without this option, only show the planned changes",
    )
    args = parser.parse_args(argv)
    manifest_path = args.manifest.expanduser().resolve()

    try:
        targets = load_repositories(manifest_path)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if not targets:
        print("No repositories listed; nothing to do.")
        return 0

    changes, errors = collect_changes(targets)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        print("No permissions changed because repository inspection failed.", file=sys.stderr)
        return 1

    action = "Applying" if args.apply else "Dry run; would apply"
    for path, old_mode, new_mode in changes:
        print(f"{action}: {path} ({old_mode:04o} -> {new_mode:04o})")

    if args.apply:
        failed = False
        for path, _, new_mode in changes:
            try:
                os.chmod(path, new_mode, follow_symlinks=False)
            except OSError as error:
                print(f"error: could not change {path}: {error}", file=sys.stderr)
                failed = True
        if failed:
            return 1
        print(f"Updated {len(changes)} path(s).")
    elif not changes:
        print("All supported repository paths already have owner-write permission.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
