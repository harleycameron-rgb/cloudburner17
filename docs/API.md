## Existing runtime

The existing supervisor, admission and spherical routes in `backend/main.py`
are unchanged. SCANDOC does not call them or attach to their lifecycle.

## SCANDOC: local synthetic HTML sandbox

Open `/scandoc` (also `/scandoc/`) on the existing FastAPI application.
`backend/vercel.json` routes `/scandoc` and its assets to the self-contained
FastAPI `scandoc_page.py` function in the **existing** Vercel project's `backend`
root and explicitly includes `scandoc/**` assets. The full application mounts
the same router. Keep the linked `waxtablet/cloudburner17`
project (`prj_BvHWk06AfoyC9qsuqaLwg4VHj5ib`); Git preview automation handles
the integration branch. No separate project, production promotion or merge
is required. Native paths still route to `main.py`; these require the existing
parent `src` runtime to be packaged by the deployment environment. SCANDOC's
standalone function does not depend on those outside-root files. The existing
`/` console remains separate and unchanged in the full application; native
Vercel runtime packaging is not claimed verified by the sandbox preview.

The page uses only allowlisted, preloaded assets at `/scandoc/{asset}`.
Preloading occurs before Supervisor installs its process-wide filesystem
guard. No runtime file reads, storage, API calls, AI keys or transmissions
are added. CSP sets `connect-src 'none'`; exports require explicit local
download actions. Do not paste confidential telemetry into the local hook.

### Model and adapter

`backend/scandoc/model.js` defines `scandoc-synthetic/1`, with all demonstration
parameters committed in `modelDigest`. The inspected main source revision is
`ed9e5d68a9500eb506a5deba87adab9343f6505a`; a source commit is **not** a burn
receipt. No origin hash or genesis receipt is invented.

The `tentacled-sphere-names/1` adapter accepts exactly the eight named channels
from `src/tentacled_sphere.py`: TAP_CONVEX, SURFACE_CONCAVE, GAIN_PSYCHOSOCIAL,
HABITATAT_DOMAIN, TIME_CHRONO, SPACE_CHRONO, SCANROOT_LINEAGE, SCANDOCZERO_AUDIT.
Supplied values remain unverified; the adapter makes no six-to-eight assignment.
Cube faces are independently named +X, −X, +Y, −Y, +Z, −Z. Channel mappings and
measured evidence are unresolved. The Python source's wall-clock timestamps
are not imported into this deterministic demonstration or its AI seed.

The declared Cartesian origin `[1024,1024,0]` preserves the default shared
origin of `src/spherical_topology.js`. Sphere centers are absolute coordinates
in that frame; subtract the declared origin for relative displacement. Radius
is measured around that center in diagnostic units, **not** distance to origin.
Sentinel is fixed at that origin and its separation is reported independently.
There is no measured frame calibration or external app alignment.

Baseline face centers are `B_i = C + ell0 * Q * n_i`, for the six signed unit
axes. `Q` must be proper orthonormal (determinant +1, tolerance 1e-9) and `ell0`
positive. Anchors remain fixed. `median_core` sorts six
`norm(position_i - B_i)/ell0` values and averages the middle two. Individual
residual vectors stay inside the verifier; neither they nor face positions,
source channel payloads or raw telemetry enter the context seed.

The complete final Cube commitment includes the entire versioned model,
final tick state, center/orientation/half-extent, eight vertices and six
ordered face polygons. Per-face hashes bind model, frame, time/tick, anchor,
face identity and position. The trajectory contains all six face centers,
fixed anchors, Sphere center/radius/velocity, Sentinel, frame, units and time
at every tick; it is recursively frozen. SHA-512 commits canonical UTF-8 JSON
(sorted object keys, array order retained, finite JSON numbers only).
These are unsigned integrity diagnostics, not credentials. No custom
three-pass SHA512 bundle is emitted or misrepresented as standard SHA-512.

### Frequency and visual layers

`synthetic-phase/1` fixes **0.25 cycles/synthetic-second**, epoch 0 and phase0 0:
`phase(t) = phase0 + 2*pi*value*(t-epoch)`. It is a committed synthetic model
parameter, not a trajectory-derived or physical frequency. Changing it changes
the model and Cube commitments but not the trajectory. Evolution is separately
versioned as `linear-demo/1`: five ticks at one synthetic-second intervals;
initial center offset `[2,0,0]`, velocity `[-0.1,0,0]` diagnostic-units per
synthetic-second, radius `1 - 0.05*t`, face half-extent `1 - 0.05*t`.
No hidden-state injection or physical convergence is claimed.

The CMB-inspired 0.1137 constant is inert metadata, not calibration.
Spiral-back and pyramid-nose are declared visual-only layers, not measured
paths; they are not drawn as trajectories. Torsion is disabled and non-null
torsion rules are rejected until an explicit versioned implementation exists.

### v0.6 read-only boundary and handshake

`v0.6-local/1` is a new diagnostic policy, not a claim that existing native
lifecycle contracts implement v0.6. It checks exactly six ordered finite faces,
proper baseline, fixed anchors/Sentinel, consistent origin/frame/units,
positive Sphere radius, increasing safe-integer ticks and finite increasing
time, and finite-difference center velocity. Closure uses the **maximum**
distance of final face centers to the final Sphere center, not an average.
The inward closure rate is the decrease in the six-leg mean radius relative
to Sphere center divided by elapsed time and must be strictly above epsilon.
Missing six/seven values or either near-zero denominator remain unresolved;
the policy does not invent the missing measured ratio definitions.
Containment requires `0 <= residue <= inner <= outer`. Endpoint proximity
uses the **actual final sample**, not an extrapolated intersection.
Optional `segment: "linear"` reports the bounded last segment's proximity
separately and never substitutes for endpoint proximity.

Missing measured evidence, endpoint, origin hash or receipt is unresolved;
failed checks are rejected. Even caller-supplied “measured” claims cannot be
authenticated here and remain unresolved. No verdict authorizes burn, seal,
axis advancement, Structural Melting attachment, admission or retirement.
Existing gates and receipts are untouched.

`contextSeed(demo)` explicitly bootstraps a **local synthetic checkpoint**,
not trusted external authentication. Store its result independently before
accepting untrusted proposals. `createController(demo, trustedCheckpoint)`
checks the canonical full seed hash, model/Cube/trajectory commitments and
observed geometry before freezing its own copy. A changed full body, including
added fields, fails the `suppliedFiringResult` hook even if a caller reuses the
original seed hash. A production measured-receipt trust adapter is intentionally
absent; this controller supports only local synthetic checkpoints.

The allowlisted seed includes frame/units, fixed Sentinel, generated Cube
commitment, model commitment, eight unresolved channel names, scalar median,
observed center/radius/velocity prefix, baseline, policies and frequency.
Missing origin hash and burn receipt remain unresolved. The request hook
returns JSON locally; it never sends it. The supplied-result hook accepts only
consecutive next ticks after the frozen observed prefix, validates geometry
and time/velocity, and stores immutable proposals in a separate replaceable
forecast stream. A forecast is unverified, never observed firing evidence.
The forecast response also includes the same read-only boundary diagnostics;
passing geometry input checks does not mean closure or measured evidence passed.

### Reproduce local exports

From the repository root:

```sh
node examples/scandoc.mjs > /tmp/scandoc-demo.json
node examples/scandoc.mjs --csv > /tmp/scandoc-demo.csv
```

JSON contains complete Cube/model/trajectory and all digests. Each CSV row
contains tick/time, Sphere center/radius/velocity, Sentinel separation, median,
frequency and units, **final** complete Cube/per-face digests, full trajectory
digest, length/time units and synthetic provenance. CSV digests are final-run
commitments, not per-tick Cube commitments. Both formats explicitly label the
data synthetic. Default final tick/time is 4, center `[1025.6,1024,0]`, radius
0.8, velocity `[-0.1,0,0]`, Sentinel separation approximately 1.6, and median
approximately 0.2 (floating-point rounding is retained). Max-distance closure
fails with the default threshold 2; missing measured evidence remains unresolved.

### Validation record (isolated development workspace)

Workspace: `/tmp/scandoc-validation`; Node v24.21.0, Python 3.12.3.
Python commands used `/tmp/scandoc-venv/bin/python` with
`PYTHONDONTWRITEBYTECODE=1`. No production endpoints were exercised.

| Exact command (from workspace root) | Result |
| --- | --- |
| `node --test tests/scandoc.test.js` | 6 passed, 0 failed/skipped |
| `python -B -m pytest -p no:cacheprovider backend/tests/test_scandoc.py -v` | 2 passed; 1 upstream TestClient deprecation warning |
| `npm test` | 77 passed, 0 failed/skipped |
| `python -B -m unittest discover -s tests -v` | 51 passed, 0 failed/skipped |
| `python -B -m pytest -p no:cacheprovider backend/tests -v` | 7 passed, 0 failed/skipped; same warning |
| `python -B -m unittest discover -s backend/tests -v` | 4 passed; unittest does not collect the three function-style tests (pytest does) |
| `python -B src/run_supervised_build.py` | exit 0, local stub pipeline completed |
| `PYTHONPATH=src python -B -c "from autonomy import self_verify; assert self_verify()"` | exit 0 |
| `python -B -m src.stabiliser` | exit 0 |
| `python -B -m src.harmony` | exit 0 |
| `python -B -m src.autonomy` | exit 0 |
| `python -B -m src.agent_core` | exit 0 |
| `docker build -t scandoc-validation -f backend/Dockerfile .` | exit 0 |
| `docker run --rm -d --name scandoc-smoke -p 18000:8000 scandoc-validation` | local container started |
| `curl --fail --silent --show-error -X POST http://localhost:18000/supervise/burn/y` | existing CI local stub smoke: completed; not a physical firing |
| `curl --fail --silent --show-error -D /tmp/scandoc-headers.txt http://localhost:18000/scandoc -o /tmp/scandoc-page.html` | HTTP 200, transmission-blocking CSP |
| `curl --fail --silent --show-error http://localhost:18000/scandoc/model.js -o /tmp/scandoc-served-model.js` | HTTP 200, bytes match source |

Initial Python attempt failed: `python -B -m pytest backend/tests/test_scandoc.py -v`
reported `No module named pytest`; FastAPI was also absent. The temporary venv
installed advisory-checked FastAPI 0.143.1, Uvicorn 0.54.0, pytest 9.1.1 and
httpx 0.28.1; no dependency files were changed. These resolved the missing
dependencies. TestClient warns about upstream httpx deprecation; no new httpx2
dependency was introduced. The root `verifyTimestampProof.test.ts` contains
four Jest-style tests but the repository has no Jest/TypeScript runner or
script configured and `jest` is unavailable: those tests were **not run**.
An explicit attempt, `node --test verifyTimestampProof.test.ts`, exits 1 with
`ERR_MODULE_NOT_FOUND` for its extensionless `./verifyTimestampProof` import;
none of its four Jest-style cases executes. No unrelated tests were changed.
No separate linter/build script exists in package.json.

Playwright MCP failed with `Transport closed`; interactive browser validation
is unavailable, not passed. HTTP smoke and focused model/controller tests ran
instead. GitHub run 38631060265 reported `action_required` with zero jobs and
no failed-job logs; main runs 38487176694 and 38487176642 were successful.

The backend-only packaging smoke copied only `scandoc_page.py` and `scandoc/`
to `/tmp/scandoc-backend-only`, then ran:

```sh
PYTHONDONTWRITEBYTECODE=1 /tmp/scandoc-venv/bin/python -B -c "from fastapi.testclient import TestClient; from scandoc_page import app; c=TestClient(app); assert c.get('/scandoc').status_code == 200; assert c.get('/scandoc/model.js').status_code == 200; assert c.post('/supervise/burn/y').status_code == 404; print('backend-only preview smoke passed')"
```

This passed without `src` or the native application. Docker was rebuilt and
the integrated asset route rechecked after splitting the router.

Local demo output files were emitted at `/tmp/scandoc-demo.json` and
`/tmp/scandoc-demo.csv` (not committed). Final complete Cube digest:
`1f6f88e0b6955c0e71bbbf3bc8119b43530cda4f5527dad977752fc76476705de3c8919e34f605ce41c97f56b91967f194455b93786fc96340cd5d34ff93550b`.
Trajectory digest:
`56265ceea99981f7e5ae04017cea6c79abdae0a9d80b82eaa1fbca7e0185d9b2b816528531ce75f97d38395bf91af1c6bd5d232ed4695ec1b43e2f908fffc7b7`.
Per-face digests and complete provenance are in both exports.

The existing project's Git automation reported a Ready preview at
<https://cloudburner17-git-copilot-prj-bvhwk06afoyc9qsu-9da359-waxtablet.vercel.app/scandoc>
on PR #34. No project was created or production promoted. A direct public
preview request could not resolve DNS in this sandbox, so public runtime
availability is not claimed verified.

CodeQL reported zero Python/JavaScript alerts. The parallel automated code
review binary was unavailable; an independent read-only review identified
the outside-root runtime packaging dependency. Splitting the standalone
SCANDOC entry point and explicitly packaging its assets addresses that finding
for the new preview surface without copying or changing native lifecycle code.
The follow-up independent review found no significant issues. A requested
parallel-validation rerun reported “no changes since last review/run” and
skipped both analyses; this is not represented as a fresh final CodeQL scan.
Latest inspected PR workflow run 38633202126 also reports `action_required`
with zero jobs/no failed-job logs. GitHub CI is awaiting action, not passed.
The bot's updated Ready preview deployment is
<https://vercel.com/waxtablet/cloudburner17/CXuYspiCLfYgXKgnrfndFNT7pscD>.
