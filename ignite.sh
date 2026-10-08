#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "$0")"

export PYTHONDONTWRITEBYTECODE=1

echo "== CLOUDBURNER17 :: Runtime Ignition Sequence =="
echo "→ Executing supervised pipeline demo..."
python -B src/run_supervised_build.py

echo "→ Running event-model validation tests..."
python -B -m unittest discover -s tests -v

echo "→ Verifying autonomous cycle and reproducible sentinel..."
PYTHONPATH=src python -B -c "from autonomy import self_verify; assert self_verify()"

echo "== CLOUDBURNER17 :: Ignition Complete =="
echo "All systems stable. Residue = 0, Drift = 0."
