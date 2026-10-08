# CLOUDBURNER17 — Zero-Data Invariance Engine

CLOUDBURNER17 is a deterministic, zero-data surface-to-core invariance engine
for supervised execution, reproducible sentinels, and drift-aware harmonic
cycles. Engine state, benchmark results, and adapter buffers remain transient
in memory. The runtime makes no network or external-state calls and does not
persist application data, reports, or logs.

The repository also includes the multi-agent invariant admission contract,
living-invariant predicates, modular torsion/hash commitment specification, and
textual system maps. The files under `binaries/` are placeholders, not
executable programs.

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
- `src/multi_llm_scheduler.py`: task, LLM-weight, and timing alignment
- `src/admission.py`: cycle-based topology continuity and live submission checks

The Waxtablet adapter retains transient state in its process; it is not
stateless between calls, but does not persist that state.

## Invariant system ingestion assets

- `engine/invariant_contract.txt`: curvature/topology preservation,
  massless-state observation, torsion commitment, false-invariant counting,
  and base admission contract
- `engine/life_axiom.txt` and `engine/admission_predicate.txt`: life valuation
  and final admission predicates
- `runtime/`: ignition sequence and v0.3.1 stabilization specifications
- `system/`: topology, curvature, residue, massless-state, torsion, hash,
  cycle, and candidate-registry contracts
- `BINARIES.md` and `binaries/`: inventory and non-executable binary
  placeholders

See [`CHANGELOG.md`](CHANGELOG.md) and [`release/`](release/) for release
history and notes.

The executable admission and torsion APIs are implemented in
`src/admission.py`; see [`docs/INVARIANT_SPEC.md`](docs/INVARIANT_SPEC.md).
The backend accepts live admission payloads at `POST /admission`; the Waxtablet
adapter exposes the same check through its `admission` action. Burn diagnostics
include the adaptive curvature gain.
The backend also exposes `GET /runtime`, a zero-mutation ignition status
snapshot. Run `bash ignite.sh` from any directory to execute the supervised
pipeline, test suite, and autonomous-cycle verification.
The text assets specify contracts and schemas and do not alter runtime
persistence behavior.

### JavaScript test-result ingestion

`src/ingest.js` exports `ingestTestResults(results)`, and `src/runtime.js`
exports `runtimeIgnition(results)` and the live feed helpers as ES modules.
Ingestion and ignition accept an array of records with a string `name` and a
boolean `ok`; malformed inputs throw `TypeError`. They leave the input unchanged
and retain no state between calls.

Ingestion returns `passed`, `failed`, `invariantPulse`, and an ordered `vector`
of `{ name, ok, timestamp }` records. Timestamps are epoch milliseconds sampled
once per batch, so they are nondecreasing within that vector. Runtime ignition
returns the vector, `invariant`, `residue`, `drift`, and a string `status`:
`IGNITION_STABLE` when all results pass, otherwise `IGNITION_VARIANT`. Residue
and drift each equal the number of failures. Empty input has a true invariant
and zero residue/drift, but does not open the feed.

`canFeed(ignition)` opens only for a nonempty, stable vector.
`beginFeedCycle(source)` pulls one batch and returns an active feed or a halted
result. `harmoniseTriStream`, `stabiliseContradiction`, and `proofRhythm`
provide ordered projections of the ignition vector. The async
`CLOUDBURNER17_ORCHESTRATE(source)` pulls once and returns ingestion, ignition,
feed status, all three projections, and the organism status.

This API operates entirely in memory, independently of the Python supervisor;
it does not install the Python process-wide filesystem guard.

### Agent-side live feed invocation

The root-level `CLOUDBURNER17.js` entry point exports the same orchestrator.
From an ES module in the repository root:

```js
import { CLOUDBURNER17_ORCHESTRATE } from "./CLOUDBURNER17.js";

const source = {
  async pull() {
    const response = await fetch("https://your-endpoint/runtime-feed");
    if (!response.ok) {
      throw new Error(`Runtime feed HTTP ${response.status}`);
    }
    return response.json();
  },
};

CLOUDBURNER17_ORCHESTRATE(source)
  .then(report => console.log(report))
  .catch(err => console.error("ORCHESTRATION_ERROR", err));
```

Replace the placeholder URL with your runtime feed endpoint. It must return a
JSON array of `{ name: string, ok: boolean }` records, not the backend's
`GET /runtime` status object. The agent-owned source performs the network call;
the orchestrator only calls `source.pull()` once and processes its batch in
memory. Source, HTTP, JSON parsing, and payload validation errors reach the
caller's `.catch()` handler. Importing the entry point does not start a feed.

### Safety continuity

The entry point also exports `safeFeed(source, orchestrate)` and
`continuityLoop(source, orchestrate)`. Pass `CLOUDBURNER17_ORCHESTRATE` as the
orchestrator: these helpers pull once per pulse and pass the resulting batch
directly to it. The orchestrator accepts either a source or an already-pulled
array, with the same validation and report shape.

Continuity rejects updates less than 150 ms apart, vector-length changes from
the last accepted state, and nonzero drift. The loop logs each safe pulse,
waits 150 ms, and stops at the first continuity violation. Continuity state is
process-wide, shared by all calls; rejected audits after the interval check
also advance the rate-limit timestamp. Source and orchestration errors
propagate to the caller.

## Run and verify

Run the JavaScript scenarios with Node.js 18 or newer using `npm test`.
No dependency installation is required. The Python checks remain:

```sh
PYTHONDONTWRITEBYTECODE=1 python -B src/run_supervised_build.py
PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tests -v
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -B -c \
  "from autonomy import self_verify; assert self_verify()"
```

The supervised build prints the sentinel. Identical inputs and step order
produce the same value. See [`docs/zero_data_contract.md`](docs/zero_data_contract.md)
for the runtime rules.

The `CLOUDBURNER17 Pipeline` GitHub Actions workflow runs the JavaScript tests
on pushes to `main` with Node.js 20, alongside the existing zero-data workflow.

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
