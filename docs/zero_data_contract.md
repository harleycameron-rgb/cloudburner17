# Zero-Data Contract — CLOUDBURNER17

- No application data writes or persistent application storage at runtime.
- Runtime engine operations and results occur in memory.
- Deterministic execution only.
- Sentinel hashes must be reproducible.
- No application external-state calls or persistent logs.
- Deployment infrastructure may store container images outside the engine
  runtime; the application container is not configured with a data volume.
- Harmony and stabiliser modules enforce invariance.
