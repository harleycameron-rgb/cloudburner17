# Tentacled sphere creation

`node examples/tentacled-sphere.mjs` creates an in-memory sphere with eight
curved arms. Each arm attaches at its native spherical placement and depends
on a common core. All nine modules execute admission, convergence, retirement
and burn before their envelope is checked. Curve parameters are bounded.

`createTentacledSphere` is exported from `src/tentacled_sphere.js`. It returns
geometry and locally verified receipts. These are diagnostic temporal anchors;
no sensor streams or semantic assignments to the eight arms are implemented.
The existing six local couplers and the eight-arm geometry are distinct.

Run `node --test tests/*.test.js` and
`python -B -m unittest discover -s tests -v` from the repository root.
The bridge regression executes the real Node subprocess with two dependent
scenes and a dual shift, and checks that sample content is absent from output.

## Arm / HTML app / orrery mapping

Inspection found the supervisor console in
`harleycameron-rgb/cloudburner17:frontend/index.html` (loading `frontend/app.js`)
and the inline supervisor/spherical page in `backend/main.py`.
Neither defines designated eight-arm apps or an orrery. No orrery implementation
or arm-to-app assignments were found in this repository. Repository references
in `topology/whole.json` are not arm assignments. External apps have not been
inspected or executed; their paths, fields, units and epochs cannot be inferred.

Each unresolved app mapping is explicitly pending, not silently replaced by
synthetic data. The separately identified local diagnostic geometry uses **T**
and **F** below. Every arm is **synthetic-tested**, not integration-tested.

| Arm ID | Repository and HTML file path | Orrery source fields, units and time reference | Geometric transformation | Shared coordinate frame and origin | Source commitment and geometry commitment |
| --- | --- | --- | --- | --- | --- |
| arm-1 | Pending | Pending | Orrery: pending; diagnostic: T | Orrery alignment: pending; diagnostic: F | Orrery: null/pending; diagnostic: S1, G1 |
| arm-2 | Pending | Pending | Orrery: pending; diagnostic: T | Orrery alignment: pending; diagnostic: F | Orrery: null/pending; diagnostic: S2, G2 |
| arm-3 | Pending | Pending | Orrery: pending; diagnostic: T | Orrery alignment: pending; diagnostic: F | Orrery: null/pending; diagnostic: S3, G3 |
| arm-4 | Pending | Pending | Orrery: pending; diagnostic: T | Orrery alignment: pending; diagnostic: F | Orrery: null/pending; diagnostic: S4, G4 |
| arm-5 | Pending | Pending | Orrery: pending; diagnostic: T | Orrery alignment: pending; diagnostic: F | Orrery: null/pending; diagnostic: S5, G5 |
| arm-6 | Pending | Pending | Orrery: pending; diagnostic: T | Orrery alignment: pending; diagnostic: F | Orrery: null/pending; diagnostic: S6, G6 |
| arm-7 | Pending | Pending | Orrery: pending; diagnostic: T | Orrery alignment: pending; diagnostic: F | Orrery: null/pending; diagnostic: S7, G7 |
| arm-8 | Pending | Pending | Orrery: pending; diagnostic: T | Orrery alignment: pending; diagnostic: F | Orrery: null/pending; diagnostic: S8, G8 |

**T:** `native-radial-helical/1`. Native `radialPlacement` derives longitude
and colatitude (radians) from the declared scene's topology hash, not orbital
data. With native direction `d`, normalized `u = cross(reference,d)` and
`v = cross(d,u)`, sample `t = j/segments` produces
`origin + radius * ((1+length*t)*d + amplitude*t*(cos(2*pi*turns*t)*u + sin(2*pi*turns*t)*v))`.
Length and amplitude are dimensionless radius multiples, turns are revolutions,
and segments are a count. No orbital epoch or time evolution is implemented.

**F:** Native Cartesian diagnostic frame from `source.sphere`, with default
origin `[1024,1024,0]`, axis `[0,0,1]`, tilt `pi/6` radians and radius `1`.
Positions use arbitrary diagnostic units, not astronomical units or metres.
Caller-supplied sphere values are recorded in each trace; no astronomical
reference-frame alignment is claimed. Time reference is null. Native lifecycle
timestamps are `Date.now()` Unix epoch milliseconds, not orrery observation time.

**Si / Gi:** `arms[i-1].sourceCommitment` and `.geometryCommitment` are SHA-512
hex digests of UTF-8 `JSON.stringify` in the construction field order.
Si commits `trace.source`: its synthetic kind, declared scene and topology hash.
Gi commits `{schema:"tentacled-sphere-geometry/1", id, mapping, trace,
sourceCommitment, attachment, points}`. It binds the pending mapping, source,
transformation, frame and resulting geometry. Neither is an app/orrery receipt.
The native `receipt` remains separate and session-specific.

“Geometrically logged” means only the returned, in-memory `trace` connecting
source, transformation and arm geometry, with those commitments. No file,
network or storage writes occur. The example explicitly prints local JSON;
durable export requires an explicit user action such as redirecting that output.
These hashes are unsigned integrity diagnostics, not privileges or credentials.
Status `declared` would describe an unexercised assignment; `synthetic-tested`
describes this tested local pathway; `integration-tested` requires executing the
actual designated app-to-orrery-to-arm pathway, which remains pending.

## In-memory synthetic Python scores

`modules/synthetic_geometry.py` adds the supplied `SyntheticGeometry`
generators for TAP, SURFACE, GAIN, HABITATAT, TIME, SPACE, SCANROOT and
SCANDOCZERO, in that order. `in_memory=True` describes their execution:
`run_cycle()` returns a new dictionary without storage or network operations.
The module exposes `GEOMETRY` and `IN_MEMORY_RESULTS`; importing it does not
print. Explicit execution with `python -B modules/synthetic_geometry.py`
prints the dictionary locally.

Defaults remain `seed=1.0` and `delta=0.1137`. Every cycle restarts from the
seed and increments it after each function without modifying the seed.
The shared score is `round(abs(x*y*z) * 0.1137, 6)`, a non-physical custom
score, not measured curvature. Function labels are declared synthetic names,
not verified planetary, psychosocial, lineage or HTML-app relationships.
Tests exercise all eight supplied formulas, repeatability and the existing
zero-data guard.

These scores do not feed the JavaScript arms or establish an app-to-orrery-to-arm
integration. The mapping table, physical units, time references, coordinate
alignment and HTML paths remain pending. Zenodo publication remains disabled:
no deposit workflow is added. Physical interpretation/curvature verification
and HTML mapping must be completed before publication is reconsidered, and
record-specific owner approval is still required.

## Authentication boundary

This module does not issue credentials, authenticate users, grant repository
permissions, or call other legs. Production routing must use `engine.input`
and backend-supplied authentication, destination authorization, transition-gate
verification, and execution revalidation. Local envelope integrity is not
proof of identity, consent, or signed qualification. Signature and Bitcoin
anchor fields remain null. Upstream integration is explicitly false.
Existing routing and authorization code is unchanged; no production
authentication or cross-repository integration is added here.

## Deposit status

This is source preparation, not a published Zenodo deposit. Licence selection,
final inventory/rights/privacy review, upstream integration where supported,
release packaging, and record-specific owner approval remain outstanding.
No publishing, deployment or automatic merge is performed.
