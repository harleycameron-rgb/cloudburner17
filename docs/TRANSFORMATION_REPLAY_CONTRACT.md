# Bounded transformation and replay contract

This contract describes numerical diagnostics for declared synthetic/browser
geometry and the existing in-memory record verifiers. It does not qualify a
physical system, infer an astronomical frame, authenticate a source, or enable
any live gate or write.

## Geometry metrics

`TentacledGeometry.comparePointClouds(before, after)` is used by the browser
audit page and is also exercised directly by Node tests. Each cloud supplies
finite 3D `origin` and `{id, position}` records, a nonempty `units` label, and
optionally an `edges` array. The implementation accepts at most 64 points and
2016 undirected edges to bound its pairwise work. Records are matched by unique
ID, so array and undirected-edge order do not affect the reported relations.

The function returns measurements rather than a pass/fail equivalence claim:

- `maxRadialError`: maximum absolute change in distance from each cloud's own
  origin, over matched IDs, in the declared coordinate units.
- `pairwiseDistanceChanges`: every matched ID pair's before/after distance and
  signed change; `maxPairwiseDistanceChange` is the maximum absolute change.
- `missingBefore` and `missingAfter`: IDs present only in the other cloud.
- `topologyPreserved` and `changedConnectivityEdges`: exact equality and
  symmetric difference of explicitly supplied, simple, undirected edge sets.
  These are `null` when either cloud omits connectivity.

No tolerance is applied by the metric function. The browser's existing
`1e-10` configured-radius-unit display threshold remains a numerical UI guard,
not a scientific or measurement tolerance. The asymmetric fixture uses
`diagnostic-unit` coordinates of order one; 100 repeated inverse rotations
remain below `1e-12` in both measured errors, while a `5e-12` injected radial
change is separately observable. Those checks justify only regression
sensitivity for this fixture and JavaScript floating-point path. They do not
calibrate external inputs. One Node.js 22.23.4 run observed repeated-cycle
maxima of `2.043e-14` radial and `2.088e-14` pairwise. The `1e-12` regression
bound is about 48 times those observations, while the existing `1e-10` UI
threshold is about 4,800 times larger. These margins describe only this
runtime and fixture, not a physical tolerance. Test-failure counts are
reported by the test runner, not conflated with geometric drift.

Transformation disposition for the fixed fixture:

| Transformation | Metric contract | Exact-record disposition |
| --- | --- | --- |
| Rigid rotation | Radial and pairwise distances remain invariant within measured floating-point error; connectivity unchanged. | Coordinates change, so the record digest changes. |
| Joint point/origin translation | Relative radii and pairwise distances remain invariant within measured error. | Absolute coordinates change, so the digest changes. |
| Local surface twist | A single point can retain its radius while changing pairwise distances. | Changed coordinates change the digest. |
| Record/edge reordering | ID-matched relations and undirected connectivity are invariant. | Array ordering is committed; the digest changes. |
| Reflection | Radii and pairwise distances are invariant, but the fixture's oriented volume changes sign. | Coordinates and digest change; distance descriptors cannot distinguish chirality. |
| Connectivity change | Geometry metrics may remain unchanged; edge-set symmetric difference reports the graph change. | The changed record digest differs. |

These are explicit mathematical controls for the fixture, not evidence that
the transformations preserve an application's physical meaning. A local
twist is not presumed to preserve pairwise distance. Exact edge-set equality
is the only graph/topology property asserted here; radius preservation,
distance descriptors, spectra, or hashes do not establish topology or
physical identity. No persistent-homology dependency is used.

## Content, replay, and trust

Structural metric agreement is separate from exact record content. Canonical
hashes commit data according to their existing serialization rules; they can
detect altered content or link a locally replayed record, but do not establish
physical identity, provenance, authentication, trusted time, or physical
validation.

The backend research-receipt verifier recomputes the record and replay
commitments and rejects internally rehashed inconsistent payloads. Spherical
envelope and sphere-shift verifiers validate ordered event histories against
an independently retained expected head; truncated, reordered, replaced-head,
and altered records are rejected by existing tests. The browser audit receipts
remain locally generated SHA-512 digests, not signatures. Research labels stay
`UNVERIFIED`, the live gate stays `CLOSED`, and sphere writes remain disabled.
Timestamps, random session IDs, and services are not used in the deterministic
geometry fixture or its metrics.

## Workstream ledger

| Workstream | Implementation evidence | Gap and disposition | Verification | Status |
| --- | --- | --- | --- | --- |
| 1. Transformation contracts | `backend/portal/audit/web/geometry.js` keyed point-cloud metrics; asymmetric controls above. | Synthetic mathematical contracts only; no real-world frame or physical-preservation assertion is justified. That remains explicitly outside this diagnostic implementation. | `tests/audit_geometry_contract.test.js`: rotation, joint translation, twist, reorder, reflection, and connectivity controls. | VERIFIED (bounded scope) |
| 2. Structure vs record identity | Metric comparison matches stable IDs and order-independent edge sets; protocol SHA-512 digest tests show reordered, rotated, reflected, and connectivity-altered records have different digests. | Neither relation metrics nor digest authenticates or identifies a physical object. | Geometry contract tests plus spherical envelope and backend replay tests. | VERIFIED (distinction preserved) |
| 3. Drift and tolerance | Reports max radial and pairwise-distance changes with explicit coordinate units; UI threshold is labeled and separate from measured values. | `1e-10` is a local numeric display threshold, not an empirically validated measurement tolerance. No external calibration data exists. | 100 inverse cycles, injected `5e-12` drift, metric-bound sensitivity assertions, and test-runner counts. | VERIFIED (numeric diagnostic only) |
| 4. Deterministic/adversarial fixtures | Fixed asymmetric in-memory data; no timestamp, random ID, or service fields. Comparison copies its inputs and rejects malformed, sparse, empty, nonfinite, oversized, duplicate, and inconsistent-unit records. | No live service or physical fixture was available or invoked. | Positive controls, injected transform/connectivity violations, mutation-isolation tests, plus existing malformed and replay tests. | VERIFIED (offline scope) |
| 5. Graph/topology properties | Exact edge-set comparison for simple undirected graphs; edge endpoints must exist, differ, and be unique. Omitted connectivity reports `null`. | Does not prove manifoldness, homology, or geometric topology; no such claim or substantial dependency is added. | Tests distinguish unchanged geometry from altered edges and verify the browser reports connectivity as not modeled. | VERIFIED (declared properties only) |
| 6. Integrity/trust boundary | Existing content hashing, replay reconstruction, retained-head checks, and explicit `UNVERIFIED`/`CLOSED`/no-write fields remain in place. | Authentication, trusted time, durable independent history, and physical validation remain unimplemented and are not represented as delivered. | `tests/test_scandoc_research.py`, `backend/tests/test_research_replay.py`, `tests/spherical_topology.test.js`, and `tests/sphere_shift_gate.test.js`. | VERIFIED (trust limitations retained) |
| 7. Runtime integration | Browser-loaded UMD geometry module now powers the audit metrics; Python/backend replay is unchanged; the npm glob discovers the new Node tests; preview test matches the existing standalone entrypoint and asset bundle. | No configured real-browser/DOM automation exists; syntax and asset tests do not claim a browser rendering or deployment test. Python admission curvature drift remains a separate state metric, not a unit-converted physical distance. | Node geometry/lifecycle tests, Python replay/preview tests, full JS/Python suites, served-asset configuration and syntax checks. | VERIFIED (available local integration) |

## Boundaries and reproduction

The Python admission code's `curvature_drift` is its sum of absolute
`kappa`-state changes; its domain units are not assigned here and it is not
interchangeable with Cartesian radial or pairwise distance. Backend trajectory
replay verifies its own serialized input contract. These interfaces remain
separate rather than asserting unsupported cross-language scientific
equivalence.

The repository's main workflow uses Node 22, runs `npm test` and the separate
TypeScript suite, and checks served-JavaScript syntax. No browser automation
configuration or browser build is present. Python CI uses Python 3.11/3.12;
local verification below used Python 3.12.3. PostgreSQL-only integration
cases are skipped locally without a disposable database. Local tests do not
verify deployment.

Research DOIs listed in the task prompt were not used to derive implementation
claims; no literature findings, certification, or endorsement are asserted.
