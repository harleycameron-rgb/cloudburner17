# CLOUDBURNER17

CLOUDBURNER17 is a zero-data, autonomous, harmonious execution engine. Its
supervised pipeline keeps step state and results in memory and does not create
persistent benchmark, superblock, burn-report, log, or state artifacts.

## Zero-data behavior

- The supervisor installs a runtime guard that rejects file-writing and
  filesystem-mutation operations.
- Step results and the execution trace remain in memory only.
- The harmony stabilizer requires the registered step order and computes a
  reproducible sentinel from canonical in-memory step results.
- Pipeline output is sent to standard output or displayed transiently in the
  frontend; it is not saved by the application.

## Run the supervised pipeline

```sh
python -B src/run_supervised_build.py
```

The pipeline executes `burn`, `ignite`, and `residue` in order. Run it again
with the same inputs to confirm that it produces the same sentinel.

## Verify zero-data enforcement

```sh
python -B -m unittest discover -s tests -v
```

The tests verify deterministic results, reject out-of-order supervised steps,
and confirm that persistent file writes are blocked. The GitHub Actions
workflow runs these checks and the supervised pipeline with bytecode writing
disabled.
