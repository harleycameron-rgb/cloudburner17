"""Explicit standalone local export; never imported by the runtime."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from .benchmark import canonical, replay, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "export"):
        command = commands.add_parser(name)
        command.add_argument("--revision", required=True)
        if name == "export":
            command.add_argument("--output", type=Path, required=True)
    verify = commands.add_parser("replay")
    verify.add_argument("input", type=Path)
    args = parser.parse_args()
    if args.command == "replay":
        if args.input.stat().st_size > 2_000_000:
            parser.error("evidence exceeds 2 MB bound")
        with args.input.open(encoding="utf-8") as stream:
            result = replay(json.load(stream))
        print(canonical(result))
        return 0 if result["status"] == "verified" else 1
    evidence = run(args.revision)
    if args.command == "export":
        evidence["event"] = {"exported_at": datetime.now(timezone.utc).isoformat()}
        # Exclusive creation prevents overwriting existing evidence or following a symlink.
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(canonical(evidence) + "\n")
        print(canonical({"content_commitment": evidence["content_commitment"]}))
    else:
        print(canonical(evidence))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
