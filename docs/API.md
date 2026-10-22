## Existing runtime

The existing supervisor, admission and spherical routes in `backend/main.py`
are unchanged. SCANDOC does not call them or attach to their lifecycle.

## Tentacle Sphere introduction

Open `/tentacle-sphere` (also `/tentacle-sphere/`) from the navigation link on
the existing `/` supervisor homepage. This static introductory page retains
the homepage's simple document styling and includes a labelled visualization
placeholder and a return-home link. It is not a simulation or live integration.
It loads no scripts or external assets, performs no admission or agent actions,
burns no receipts, and saves no data. Existing API routes are unchanged.

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

`backend/scandoc/model.js` defines `scandoc-synthetic/2`, with all demonstration
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
The export emits `centerDistanceFromRadiusOrigin` separately from geometric
`sphere.radius`; the declared radius origin is `frame.origin`. Sentinel is
fixed at that origin, so its separation happens to equal center distance in
this model. Neither quantity is a substitute for geometric radius.
`originStatus: "UNRESOLVED_NO_ORIGIN_RECEIPT"` explicitly records that no origin
receipt exists. Baseline calibration is synthetic-only and the source-channel
mappings remain incomplete. There is no measured frame calibration or external
app alignment.

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

CMB temperature (K) and anisotropy (dimensionless) metadata have null values
and remain unresolved. They are separate from the arbitrary 0.1137 custom score;
none supplies physical calibration.
Spiral-back and pyramid-nose are declared visual-only layers, not measured
paths; they are not drawn as trajectories. Torsion is disabled and non-null
torsion rules are rejected until an explicit versioned implementation exists.

### v0.6 read-only boundary and handshake

`v0.6-local/2` is a diagnostic policy, not a claim that existing native
lifecycle contracts implement v0.6. It checks exactly six ordered finite faces,
proper baseline, fixed anchors/Sentinel, consistent origin/frame/units,
positive Sphere radius, increasing safe-integer ticks and finite increasing
time, and finite-difference center velocity. Closure uses the **maximum**
distance of final face centers to committed **baseline.C**, never the moving
Sphere center. Equality with `closureDistance` is sampled `CLOSED`; greater
distance is `NOT_CLOSED`. Neither classification says anything about motion.

`c6 = (previousMeanDistance - currentMeanDistance)/elapsedTime`, using six
face distances from that same fixed C. Motion is separately `CLOSING` if
`c6 > rateTolerance`, `EXPANDING` if `c6 < -rateTolerance`, or `STATIONARY`
within tolerance. A sampled closed stationary Cube is not failed closure.
`v7 = (currentSentinelSphereSeparation - previousSentinelSphereSeparation)/
elapsedTime` is a signed finite-difference radial rate, distinct from both
center velocity and geometric radius evolution. `sampled-c6-v7/1` computes
**c6/abs(v7)**. Only `abs(v7) <= rateTolerance` makes a sampled denominator
unresolved; zero c6 with valid v7 resolves to zero. A missing preceding sample
is unresolved, not invented. This ratio is synthetic, dimensionless, and does
not establish observed physical invariance.

`verifyBoundary` returns `INVALID_INPUT` for malformed geometry, configuration
or supplied evidence (including nonfinite or overflowed derived values).
Missing fields/evidence return `UNRESOLVED`. Evidence fields are optional but
strictly allowlisted: kind, receipt, originHash, residue, inner, outer, endpoint.
Supplied kind must be "measured", labels nonempty strings, bounds finite and
nonnegative, endpoint a finite 3-vector; unknown fields are invalid. Untrusted
evidence never grants authority. Containment requires
`0 <= residue <= inner <= outer`; a valid-bounds ordering breach returns the
distinct `CONTAINMENT_BREACH` status. Endpoint proximity
uses the **actual final sample**, not an extrapolated intersection.
Optional `segment: "linear"` reports the bounded last segment's proximity
separately and never substitutes for endpoint proximity.

Missing measured evidence, endpoint, origin hash or receipt is unresolved.
Actual endpoint failure returns `ENDPOINT_MISMATCH`. Even supplied claims cannot be
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
observed center/radius/velocity and origin-distance prefix, baseline, policies,
frequency, evolution and forecast policy. Policy `faces`/`source` keys contain
only formula/version labels, not face geometry or channel payloads.
Missing origin hash and burn receipt remain unresolved. The request hook
returns JSON locally; it never sends it. The supplied-result hook accepts only
consecutive next ticks after the frozen observed prefix. Envelope keys must be
exactly `body, proposals`; state keys `tick,time,frame,faces,sphere,sentinel`;
face keys `id,anchor,position`; Sphere keys `center,radius,velocity`; frame
keys `name,origin,units`; unit keys `length,time,angle`. All are required.
Unknown, identity, raw telemetry and torsion fields are rejected. Missing
torsion rules are explicitly unresolved; no growth is invented.

The committed `linear-next/1` forecast policy requires exact time `tick*step`,
linear radius `initialRadius+radiusRate*time`, linear center motion and the
source's linear face scaling. Radius/center/face comparisons use the committed
numeric epsilon (1e-9 by default). Finite arithmetic, geometry and semantic
boundary diagnostics are evaluated **before** atomic forecast replacement.
Policy violations throw `POLICY_REJECTION`; malformed input/derived overflow
throws `INVALID_INPUT`. Failed proposals leave the prior forecast and observed
prefix unchanged, including when a later proposal in a batch fails.
Accepted proposals report geometry acceptance and policy acceptance separately
from `physicalEvidence: "UNRESOLVED"`. They are immutable, unverified forecasts,
never observations. No exponential model is substituted for linear-demo.

The page provides a compact commitment/radius/velocity/frequency/median/status
summary and complete textual geometry even when canvas is unavailable. Run and
export/proposal controls are disabled while work is pending; failures reset
export/proposal access and visibly mark prior results stale. "Generate exact
next-state example" derives tick 5 from the exported current seed without
auto-submitting. Verification is a separate explicit action.

### Reproduce local exports

From `/home/runner/work/cloudburner17/cloudburner17` (or a checkout of the tested
revision recorded in `docs/scandoc-validation.json`):

```sh
mkdir -p /tmp/scandoc-corrective-artifacts
node examples/scandoc.mjs > /tmp/scandoc-corrective-artifacts/demo.json
node examples/scandoc.mjs --csv > /tmp/scandoc-corrective-artifacts/demo.csv
node examples/scandoc.mjs --proposal > /tmp/scandoc-corrective-artifacts/next-proposal.json
node examples/scandoc.mjs --report --revision "$(git rev-parse HEAD)" > /tmp/scandoc-corrective-artifacts/model-report.json
```

JSON contains complete Cube/model/trajectory and all digests. Each CSV row
contains tick/time, Sphere center/geometric radius/origin-distance/velocity, Sentinel separation, median,
frequency and units, **final** complete Cube/per-face digests, full trajectory
digest, length/time units and synthetic provenance. CSV digests are final-run
commitments, not per-tick Cube commitments. Both formats explicitly label the
data synthetic. Default final tick/time is 4, center `[1025.6,1024,0]`, radius
0.8, velocity `[-0.1,0,0]`, Sentinel separation approximately 1.6, and median
approximately 0.2 (floating-point rounding is retained). Sampled closure is
`CLOSED`, motion `CLOSING`, c6 about 0.05, v7 about −0.1 and c6/abs(v7) about
0.5. Physical evidence and missing measured endpoint/containment/origin receipt
remain `UNRESOLVED`. The JSON includes the exact exported context/seed hash,
local checkpoint and next-state example; none is burn/genesis evidence.

### Validation record (isolated development workspace)

The corrective pass started from actual reviewed head
`23ed4816e350303b4c58d62ee2f3ebeb16f513c7`. The machine-readable report at
`docs/scandoc-validation.json` records the **tested code commit**, full Cube,
per-face, trajectory, model and seed digests, final sampled values, exact
commands and outcomes. Demo files, proposal and logs are generated in
`/tmp/scandoc-corrective-artifacts`; they are synthetic and not receipts.

Workspace: `/tmp/scandoc-corrective-workspace`; Node v24.21.0, Python 3.12.3.
Python commands use `/tmp/scandoc-corrective-venv/bin/python` with
`PYTHONDONTWRITEBYTECODE=1`. No production endpoints were exercised.

| Exact command (from workspace root) | Result |
| --- | --- |
| `node --test tests/scandoc.test.js tests/scandoc_page.test.js` | 9 passed, 0 failed/skipped |
| `npm run test:typescript` | 4 passed, 0 failed/skipped; Node v24.21.0 |
| `python -B -m pytest -p no:cacheprovider backend/tests/test_scandoc.py -v` | 2 passed; 1 upstream TestClient deprecation warning |
| `npm test` | 80 passed, 0 failed/skipped |
| `python -B -m unittest discover -s tests -v` | 51 passed, 0 failed/skipped |
| `python -B -m pytest -p no:cacheprovider tests -v` | Same 51 tests passed; 44 subtests passed, 0 failed/skipped |
| `python -B -m pytest -p no:cacheprovider backend/tests -v` | 7 passed, 0 failed/skipped; same warning |
| `python -B -m unittest discover -s backend/tests -v` | 4 passed; unittest does not collect the three function-style tests (pytest does) |
| `python -B src/run_supervised_build.py` | exit 0, local stub pipeline completed |
| `PYTHONPATH=src python -B -c "from autonomy import self_verify; assert self_verify()"` | exit 0 |
| `python -B -m src.stabiliser` | exit 0 |
| `python -B -m src.harmony` | exit 0 |
| `python -B -m src.autonomy` | exit 0 |
| `python -B -m src.agent_core` | exit 0 |
| Docker build and GET-only `/scandoc` smoke | Build exit 0; page/model HTTP 200 and byte-identical model asset |
| CI `/supervise/burn/y` POST smoke | Intentionally not invoked during corrective pass: no firing/lifecycle endpoint calls |

The fresh workspace initially lacked FastAPI (`python -B -c 'import fastapi,
pytest, httpx'` failed with `No module named fastapi`). The temporary venv
installed advisory-checked FastAPI 0.143.1, Uvicorn 0.54.0, pytest 9.1.1 and
httpx 0.28.1; no dependency files were changed. These resolved the missing
dependencies. TestClient warns about upstream httpx deprecation; no new httpx2
dependency was introduced.

The root TypeScript test runner gap is fixed: the same four assertions now use
`node:test`/`node:assert`, an explicit `.ts` import and a type-only interface
import. Production `verifyTimestampProof.ts` and lifecycle behavior are
unchanged. Run `npm run test:typescript` separately on Node **22.6+** with native
type stripping (tested on Node 24.21.0); Node 18/20 CI still runs the existing
JavaScript command and does **not** claim TypeScript coverage. No new dependency
or transpiler was added. No linter/build script exists in package.json.

Early targeted corrective runs failed on test fixtures: 6/8 passed (policy-label
telemetry assertion and an insufficient overflow fixture), then 8/9 passed
(a hyphenated mock-DOM property typo). Fixtures were corrected, not removed;
the final focused run passed 9/9. Final suite counts are not inflated by these
retries or by counting unittest/pytest overlap twice.

Playwright MCP failed with `Transport closed`; interactive browser validation
is unavailable, not passed. HTTP smoke and focused model/controller tests ran
instead. Corrective-code GitHub run 38639312066 reports `action_required` with
zero jobs and no failed-job logs; GitHub CI is blocked, **not passed**.

The existing project's Git automation reported a Ready preview at
<https://cloudburner17-git-copilot-prj-bvhwk06afoyc9qsu-9da359-waxtablet.vercel.app/scandoc>
on PR #34. No project was created or production promoted. A direct public
preview request could not resolve DNS in this sandbox, so public runtime
availability is not claimed verified.

Remaining blockers: no authenticated measured evidence/origin receipt, incomplete
channel/calibration mapping, no torsion rule, no interactive-browser tool,
blocked GitHub CI and unverified native runtime packaging/public preview access.
The corrective pass requests review and stops before merge or production
promotion. Security/review outcomes for the tested revision are recorded in
the validation report rather than reusing the previous pass's results.

Final tested code revision: `51ef6fba0120dba35429f5b15894282c45082340`.
Subsequent changes only add this documentation and the recorded report. Exact
artifact byte SHA-512 values in the report are distinct from canonical model
commitments. The report's `testedRevision` is not a burn receipt. To reproduce
its `model-report.json` byte hash, use that exact revision in `--revision`,
not the later documentation commit.

Independent review found no significant issues; the corrective CodeQL scan
completed with zero Python/JavaScript alerts. The separate automated review
binary was unavailable and is not represented as a passing review. The
existing project's bot reported the corrective preview Ready:
<https://vercel.com/waxtablet/cloudburner17/GMQcNxjEfkftDVopsmWZ4WVKMmoc>.
