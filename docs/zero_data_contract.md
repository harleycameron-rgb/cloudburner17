# Zero-Data Contract — CLOUDBURNER17

- No application data writes or persistent application storage at runtime.
- Runtime engine operations and results occur in memory.
- The Python audit guard permits read-only access and import-time directory
  listing within canonical interpreter and installed-package roots, discovered
  before hook installation. Vercel `/var/task/_vendor` is included only when
  installed distribution metadata backs an already loaded module there.
  Arbitrary `sys.path` entries and application directories are not trusted.
- Relative paths, traversal, symlink escapes, mutating open modes/flags, and
  filesystem mutations remain blocked. Read-only FIFO descriptor opens remain
  available for captured subprocess output; blocked attempts remain sticky.
- Deterministic execution only.
- Sentinel hashes must be reproducible.
- No application external-state calls or persistent logs.
- Deployment infrastructure may store container images outside the engine
  runtime; the application container is not configured with a data volume.
- Harmony and stabiliser modules enforce invariance.
