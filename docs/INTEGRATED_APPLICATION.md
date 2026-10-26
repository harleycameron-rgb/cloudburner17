# Integrated research application

The main FastAPI application serves the three existing project surfaces on one
origin. `/` and `/portal` are the workspace; `/terminal` and `/geometry.html`
serve the Null Terminal clients; `/audit`, `/apps/*`, `/web/*` serve the source
audit; `/supervisor` retains the CloudBurner supervisor. Original audit firing
interlocks are preserved. Phone sensors, camera and audio remain opt-in.

The audit's pinned helical preview is `/api/tentacled-sphere`. CloudBurner's
separate geometry remains `/tentacled-sphere`; these schemas are not substituted.
`/source-manifest.json` records source pins and hashes. Static files are preloaded
before the supervisor installs the filesystem guard; requests neither read nor
write application files. The Vercel builder explicitly includes portal assets.

`POST /integration/research-run` accepts exactly `legs`, `tolerance`, `samples`.
The six names are tap/surface/gain/habitat/engine/business. It calls the Sphere's
separation and trajectory contract, recomputing centre, tolerance and provenance.
Samples are supplied, not measured or inferred dynamics. At most 512 samples
and 1 MiB are accepted. Malformed, nonfinite, outlying and nonmonotonic inputs
reject. The JSON response includes an unsigned domain-separated SHA-512 integrity
hash; no request or receipt is stored by this code. Hosting access logs are
infrastructure and are not a claim of zero platform telemetry.

Live gates remain CLOSED, sphere writes false and receipt trust UNVERIFIED.
The persistent authority store is not connected to public routes. Production
qualification, authenticated evidence, key custody, causal dynamics and a
shared sensor-to-live-firing runtime are outside this research application's
readiness. Browser receipts are downloads, not signed authorizations.

Verification: `python -B -m pytest -q backend/tests`,
`python -B -m unittest discover -s tests`, `node --test tests/*.test.js`.
The integration test uses the real zero-data lifespan in an isolated process,
checks both geometry contracts, all eight audit clients, rejected research
inputs, repeatable receipt hashes and request limits. Local PostgreSQL cases
skip without a disposable DSN; the existing PostgreSQL CI covers both stores.
