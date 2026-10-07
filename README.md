# CLOUDBURNER17 — Zero-Data Invariance Engine

CLOUDBURNER17 is a deterministic, zero-data surface-to-core invariance engine
for supervised execution, reproducible sentinels, and drift-aware harmonic
cycles. Engine state, benchmark results, and adapter buffers remain transient
in memory. The runtime makes no network or external-state calls and does not
persist application data, reports, or logs.

## Core principles

- Accuracy before satisfaction; transparency over drift
- Stabilising friction where required; zero-data containment
- Deterministic reproducibility and surface/core separation
- Stabiliser packet integrity and lifecycle awareness

The supervisor gates steps in `burn → ignite → residue` order. The stabiliser
validates output contracts and state transitions, harmony normalises lambda
vectors and smooths residue, and the autonomy layer checks canonical sentinel
hashes for reproducibility. Benchmark controls derive deterministically from
input rows; they do not use global random state.

## Modules and runtime API

- `src/agent_core.py`: supervised and autonomous agent
- `src/stabiliser.py`, `src/harmony.py`, `src/autonomy.py`: enforcement,
  alignment, and invariant cycles
- `src/benchmark_agent.py`: in-memory sphere/surface, core, and flow drift
  metrics
- `src/orchestrator.py`, `src/agent_interface.py`: unified engine facade
- `src/agent_memory.py`, `src/agent_validator.py`: transient FIFO buffer and
  sentinel drift validation
- `src/waxtablet_adapter.py`: `run`, `benchmark`, and `harmonic` actions with
  JSON-safe responses

The Waxtablet adapter retains transient state in its process; it is not
stateless between calls, but does not persist that state.

## Run and verify

```sh
PYTHONDONTWRITEBYTECODE=1 python -B src/run_supervised_build.py
PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tests -v
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -B -c \
  "from autonomy import self_verify; assert self_verify()"
```

The supervised build prints the sentinel. Identical inputs and step order
produce the same value. See [`docs/zero_data_contract.md`](docs/zero_data_contract.md)
for the runtime rules.

## Container deployment

Build from the repository root so the Dockerfile can copy both `backend/` and
`src/`:

```sh
docker build -t invariant-engine -f backend/Dockerfile .
docker run --rm -p 8000:8000 invariant-engine
curl -X POST http://localhost:8000/supervise/burn/y
```

Or use `bash infra/deploy.sh`. The backend responds with step status and does
not return arbitrary step outputs. Docker stores the built image on the host;
this is deployment infrastructure, outside the engine's zero-persistence
runtime contract. The application container has no mounted data volume.

## License

The requested license designation is **Zero-Data Open Architecture License
(ZDOAL)**. No license text has been provided or added; this designation alone
does not grant licensing permissions.
