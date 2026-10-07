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
See [`docs/zero_data_contract.md`](docs/zero_data_contract.md) for the
operating rules.

Run the autonomous agent and module checks with:

```sh
python -B -m src.agent_core
python -B -m src.stabiliser
python -B -m src.harmony
python -B -m src.autonomy
```

`src.orchestrator.Orchestrator` and `src.agent_interface.AgentInterface`
compose the supervised agent with optional in-memory benchmark records.
`src.agent_memory.AgentMemory` is a transient FIFO buffer, and
`src.agent_validator.AgentValidator` checks sentinel invariance. Benchmark
records may be provided as mappings, record sequences, or dataframe-like
objects; no dataframe or numerical library is required.

`src.benchmark_agent.BenchmarkAgent` also supports geometric benchmark rows
with three-value `x_params` and `p_params`. Its sample controls are generated
deterministically from the row values, so repeated calculations do not depend
on global random state. `src.waxtablet_adapter.WaxtabletAdapter` accepts
in-memory `run`, `benchmark`, and `harmonic` action payloads and can encode
responses as canonical JSON.
