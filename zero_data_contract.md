# CLOUDBURNER17 Zero-Data Contract

CLOUDBURNER17 and its supervised modules must comply with the following rules:

- **No disk writes:** persistent file creation, modification, or deletion is
  prohibited. Runtime guards must reject filesystem writes and mutations.
- **No logs:** the application must not write logs to files or retain them
  outside its active in-memory execution.
- **No persistence:** state, traces, intermediate artifacts, benchmarks,
  superblocks, and burn reports exist only for the current process.
- **No external state:** execution must not depend on external services,
  databases, or persistent storage.
- **In-memory outputs:** module results and supervised traces remain transient
  in-memory values; user-facing output is not saved by the application.
- **Deterministic execution:** identical inputs and registered step order must
  produce identical results.
- **Sentinel reproducibility:** canonical residue hashing must return the same
  sentinel for repeat executions with identical inputs.
- **Supervised invariance:** steps run in the registered order, and output
  shapes and state transitions must satisfy the stabiliser and harmony
  contracts.

CI runs tests with Python bytecode writing disabled and executes the guarded
pipeline and autonomy self-verification. Any attempted persistent write
rejected by the runtime guard is treated as a zero-data violation.
