# CLOUDBURNER17

CLOUDBURNER17 is a zero-data, autonomous, harmonious execution engine. It
keeps supervised state in memory, performs no external calls, and creates no
persistent artifacts, benchmark output, superblocks, burn reports, or logs.

## Deterministic supervised execution

The supervisor gates execution in the fixed `burn → ignite → residue` order.
The stabiliser validates each step's output contract and state transition; the
harmony layer normalises ignition lambdas and smooths residue values. The
autonomy substrate runs the complete cycle and checks that canonical,
in-memory residue hashing produces a reproducible sentinel.

The runtime filesystem guard blocks file opens and filesystem mutations after
the supervised engine starts. The backend serves its small supervisor page from
an in-memory response rather than reading frontend assets. Python bytecode
output is disabled by the documented commands and CI. Pipeline results are
returned in memory and displayed transiently on standard output or in the UI.

## Run and verify

```sh
python -B src/run_supervised_build.py
python -B -m unittest discover -s tests -v
PYTHONPATH=src python -B -c "from autonomy import self_verify; assert self_verify()"
```

The pipeline prints the same sentinel for identical inputs and step order.
See [`zero_data_contract.md`](zero_data_contract.md) for the operating rules.
