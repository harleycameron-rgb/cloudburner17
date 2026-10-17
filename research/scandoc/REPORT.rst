SCANDOC bounded offline falsification benchmark
==============================================

Scope and execution boundary
----------------------------

This is an isolated research module, not a runtime integration, lifecycle gate,
receipt issuer or semantic MDL implementation. Semantic annotations and numerical
geometry are separate tracks with incomparable metrics. No provider calls,
credentials, renderer, deployment, network transmission, timestamp submission or
physical coupling are used. No AGI, energy balance, universal invariance or proven
MDL attractor claim is supported. Overall research status deliberately remains
``unresolved``, including when the bounded controls execute as expected.

The checkout was clean on the supplied focused branch
``copilot/implement-bounded-offline-scandoc-benchmark``. Inspection baseline:
``cb6372d58de35c23d9460f467bbb6e954dd57e99``.
Freshly tested implementation: ``a2c7ff3d9f04c80248b99653222db36075ab4cf9``.
This report is subsequent documentation, not an origin receipt. No existing
runtime, deployment configuration, lifecycle tests or source geometry was changed.

Versioned contract
------------------

The executable fixture/policy versions are ``scandoc-fixtures/1`` and
``scandoc-policy/1``. The full configuration is embedded in every evidence body.
There is no randomness: numeric seed 1.0, delta 0.1137, four prescribed ticks at
0.1 intervals, and explicit shuffle order [2, 0, 3, 1].

* Semantic: shared core, persistent contradiction and forced generic compression.
  Identity and a bijective prefix encoding retain symbol distinctions; coarse
  encoding maps all symbols to ``generic``. Mean pairwise set Jaccard, original
  symbol counts, represented unique-symbol counts, decodable input symbols and
  discarded symbol identities are reported. These are annotation/count proxies,
  not validated semantic meaning, entropy, description length or semantic MDL.
  Contradictions remain in raw annotations even when compression hides them.
* Recorded/external: ``adapt_recorded`` accepts saved council-shaped rounds and
  separately supplied symbolic annotations. Raw replies and provenance category
  remain in memory. Failed and missing replies are retained; ordinary prose is
  unverified, never auto-attested. Annotations are human-supplied, not inferred
  by a model or semantic parser. The CLI cannot export these observations.
* Geometry: reuse eight named channels from the existing Python sphere generator,
  without projecting them onto a sphere. Rotation is (-y,x,z); a frame change
  adds (2,-3,1) after rotation. Deformation adds 0.25 to the first arm's x coordinate.
  All labeled within-tick pair distances are compared with absolute tolerance
  1e-10. Shuffling retains spatial snapshot identity and separately changes the
  adjacent-tick path-length metric. It does not imply temporal invariance.
* Residue: displacement relative to each original coordinate is split along and
  perpendicular to its radial unit vector, with both vectors/norms and additive
  reconstruction error retained. This is a coordinate-dependent decomposition,
  not a physical flux, surface-manifold residual or invariant under translation.
  A zero radial reference is explicitly unsupported. Geometry validation uses raw
  coordinates and Euclidean distance identities, not the renderer or an imposed
  sphere as independent measured truth.
* Unsupported: boundary removal/replacement lack an identified manifold/law;
  paired Tap-Surface runtime is unavailable in this checkout; pair-distance
  comparisons with fewer than two arms are unsupported, not passed.
* Recovery: fitted target is the coordinate mean of training points only.
  Calibration is the largest training distance to that target, not a statistical
  confidence bound. Held-out points are used only after fitting/calibration.
  The declared executable operator reuses ``parabolic_step_down`` with offset
  0.7 and t=0.25: its error contracts by 0.675 per step for 12 steps. Perturbation
  (0.1,0,0) is bounded by norm 0.25. This deliberately synthetic operator is not
  evidence about Tap or an MDL attractor. The prescribed sphere seed trajectory
  has no state-feedback update law: only observed stability is reported there.

Inputs reject nonfinite/non-numeric coordinates, booleans and out-of-bound sizes.
Numerical API bounds are 32 ticks, 32 arms/points, absolute coordinates <= 1e6,
32 semantic responses, 128 annotations per response and 80 ASCII characters per
symbol. Recorded prose is bounded to 100000 characters per reply and retained
only in memory. Invalid inputs raise ValueError; evidence replay rejects altered,
missing, unsupported-schema or non-reproducible evidence rather than promoting it.

Evidence and persistence
------------------------

Content and geometry use separate canonical JSON SHA-512 commitments:
UTF-8, sorted keys, compact separators, ensure_ascii=False, allow_nan=False.
The geometry commitment covers raw/transformed coordinates, identities, ticks,
times and geometry metrics. The content commitment additionally covers source
revision, versions, complete policies, semantic results, recovery inputs/results
and unresolved reasons. Local ``event.exported_at`` is outside both commitments;
it is not an attestation. Source revision is an explicit caller assertion, not a
signature or authenticated proof of which interpreter/source actually ran.

Replay checks both hashes and re-executes the installed fixture/policy version,
comparing the complete deterministic content. It does not merely accept a
self-consistent hash or an externally supplied success flag. Changed future
implementations must retain/version old policies to replay old evidence; there
is no version migration in v1. Exact replay is scoped to the tested Python
numeric environment, not promised bit-identical across all libm/platform versions.

Only the standalone ``export`` command creates a file, using exclusive creation
with no overwrite or final-component symlink following. ``run`` returns/prints
in-memory evidence. CLI replay reads at most a 2 MB evidence file. No environment
values, source inventories, recorded private responses, credentials, recovery
secrets or filesystem manifests enter exports. The recovery fields are public
synthetic experiment coordinates, not account-recovery material. Built-in
synthetic fixtures are the only export path. The runtime zero-data guard is
neither disabled nor bypassed; export is rejected if that guard is installed.
This module is not imported by backend startup.

Current-source reconfirmation versus historical reports
------------------------------------------------------

All source references below are in the inspected checkout, not assertions that
other repositories, unpublished files or historical PR branches were tested.
No ancestor history outside the available checkout is presumed complete.

* ``/home/runner/work/cloudburner17/cloudburner17/runtime/touch_surface_pair.py``
  is absent from the baseline tracked tree. No replacement or simplified paired
  runtime was introduced. Follow-up: supply its pinned source revision and
  numerical dependencies before defining executable paired-runtime experiments.
* ``bounded-mdl-residue-test`` and the reported saved sphere MDL adapter are not
  present in this checkout. Placeholder alignment/residue, stand-in agents and
  whole-series noise-floor claims cannot be independently reconfirmed here.
  They remain audit leads, not newly confirmed source defects or fresh results.
  Follow-up: obtain pinned source; audit the fit/calibration split and replace
  placeholders only in that source's own focused change. This benchmark's
  strict training-only calibration is independently tested.
* ``/home/runner/work/cloudburner17/cloudburner17/src/multi_llm_council.py:130-167``
  accepts ``rounds`` but constructs exactly one response round;
  lines 169-199 perform one chairman synthesis. ``rounds`` does not control
  iterative updates. Follow-up: define round semantics and offline request-count
  tests before claiming multi-round convergence; no unrelated council repair here.
* ``/home/runner/work/cloudburner17/cloudburner17/src/tentacled_sphere.py:74-101``
  generates prescribed coordinates and wall-clock metadata, not an autonomous
  recovery law. Only its coordinates/channel identities are reused; event time
  is excluded from deterministic evidence.
* ``/home/runner/work/cloudburner17/cloudburner17/src/benchmark_agent.py:57-58``
  supplies radial normalization; lines 77-90 supply the explicit interpolation
  operator. No claim that existing sphere/core/flow drift metrics are semantic MDL.
* ``/home/runner/work/cloudburner17/cloudburner17/backend/scandoc/model.js:52-78``
  explicitly declares synthetic evolution, absent origin receipt, unresolved
  channel mapping, no physical calibration and visual-only layers. Browser rules,
  diagnostics and any reported audio output do not establish live Tap integration
  or physical coupling. Follow-up: authenticated independent observations and an
  explicit coupling/update contract are prerequisites for such claims.
* ``/home/runner/work/cloudburner17/cloudburner17/common/receipt.py:6-22``
  binds event time into receipt commitments. Research content commitments are
  deliberately distinct from these receipts, not a modification of burn or
  provenance semantics.
  ``/home/runner/work/cloudburner17/cloudburner17/src/zero_data.py:45-61``
  remains authoritative for runtime filesystem denial.
* Historical PR #34 reports synthetic SCANDOC controls and historical validation:
  https://github.com/harleycameron-rgb/cloudburner17/pull/34 .
  PR #35's changed-file report was inspected as integration context:
  https://github.com/harleycameron-rgb/cloudburner17/pull/35 .
  PR #40 was identified as historical browser acceptance work, not evidence that
  its code exists in this tree. Their reported counts/previews are not reused as
  fresh tests. No public endpoints, model providers or browser audio were tested.

Fresh execution record
----------------------

Environment: Python 3.12.3; Node v22.23.3. Commands below ran from
``/home/runner/work/cloudburner17/cloudburner17``.

Initial environment failures were preserved, not represented as research failure
or success: root unittest ran 69 tests with one missing-httpx import error;
backend unittest had four missing-fastapi import errors. Existing dependency
declarations were then installed, without editing dependency files::

    python -m pip install --disable-pip-version-check -r /home/runner/work/cloudburner17/cloudburner17/backend/requirements.txt 'httpx==0.28.1'
    python -m pip install --disable-pip-version-check 'pytest==9.1.1'

Resolved FastAPI 0.143.3, Uvicorn 0.54.0, httpx 0.28.1 and existing pytest runner
9.1.1. Pytest was advisory-checked before installation. No new test framework was
introduced. Exact executed validation:

* ``python -B -m unittest discover -s tests -p test_scandoc_research.py -v``:
  initial 17 new tests passed; final focused execution **18 passed**, including
  the added persistence-guard export rejection test.
* ``python -B -m unittest discover -s tests -v``: **76 passed**, including all
  18 new controls/replay/persistence tests.
* ``python -B -m pytest -p no:cacheprovider /home/runner/work/cloudburner17/cloudburner17/tests -q``:
  **76 passed, 56 subtests passed**. Overlaps unittest; not additional coverage counts.
* ``npm test``: **91 passed**, zero failed/skipped.
* ``npm run test:typescript``: **4 passed**, zero failed/skipped.
* ``python -B -m unittest discover -s backend/tests -v``: **4 passed**;
  does not collect the existing function-style backend tests.
* ``python -B -m pytest -p no:cacheprovider /home/runner/work/cloudburner17/cloudburner17/backend/tests -q``:
  **8 passed, 1 failed**, one upstream Starlette/httpx deprecation warning.
  Failure is the unchanged mismatch between
  ``/home/runner/work/cloudburner17/cloudburner17/backend/tests/test_preview_config.py:15``
  expecting ``backend.scandoc_page:app`` and
  ``/home/runner/work/cloudburner17/cloudburner17/pyproject.toml:8``
  selecting ``backend.main:app``. A baseline diff of both files is empty.
  Follow-up: reconcile intended deployment entrypoint and that assertion in a
  separate change; no deployment decision is made here.

No linter/build command exists in the root package configuration. No Docker,
deployment, supervised lifecycle endpoint or timestamp service was exercised.
These are local executions, not a claim that hosted CI passed.

Review/security validation
--------------------------

Changed files passed the supplied secret scanner before each commit; no secrets
were detected. ``git diff --check`` passed. The required parallel validation
completed Python CodeQL with **zero alerts**. Its automated review backend was
unavailable (configured model missing), despite the wrapper's success label;
this is not recorded as a successful automated review. A separate read-only
code-review agent reviewed the complete baseline diff and reported no significant
issues. The existing backend entrypoint assertion failure remains unresolved and
out of scope; no research/security finding was suppressed to obtain a pass.

Small reproducible example
--------------------------

The following explicit local commands ran successfully. Choose a fresh output
filename if it already exists; overwriting evidence is intentionally rejected::

    cd /home/runner/work/cloudburner17/cloudburner17
    python -B -m research.scandoc export --revision a2c7ff3d9f04c80248b99653222db36075ab4cf9 --output /tmp/scandoc-falsification-example.json
    python -B -m research.scandoc replay /tmp/scandoc-falsification-example.json

Replay returned ``{"scope":"synthetic replay only","status":"verified"}``.
For current-source runs, pass the actual checked-out full Git SHA instead.
No evidence file is committed. The tested example's deterministic commitments:

Content::

    488ad63e6e7144bc0133d38e6dbfefc5ccd5e4a7df92d791841e30728d547b5ad2308fafc9a3ebac77ce3520e4314778a98d38c00dad0503347b477291a18987

Geometry::

    77e5fa0070c5e9f1814a102c2c709303c620ff6e57ce8869c13d365a2953fbbd94c4b01aa19a2e27facb7336589d350f5ec57e8d1bbf6d74b3b6d3358e367a13

Fresh observations:

* Forced generic compression: overlap 0 -> 1, retained distinctions 1 -> 0.
* Persistent contradiction remains recorded in every representation variant.
* Rotation max pair-distance error 0; changed coordinate frame
  4.440892098500626e-16.
* Deformation error 0.21336247666725694, explicitly falsified.
* Time shuffle spatial error 0, path-length change 3.7223950609821057.
* Synthetic perturbation errors after 12 steps:
  0.0008946337419569443 and 0.0008946337419569444.
* Overall research claim remains unresolved.

Tests additionally recompute SHA-512 independently using standard JSON/hashlib,
reject rehashed forged success/policy/metrics, change held-out data adversarially
without changing fitted target/calibration, and prove zero-data persistence
denial. Replay verifies this bounded computation, not authenticity of observations.

Remaining research questions
----------------------------

What independently validated distinctions should a semantic code preserve?
What description-length code and decoding/error contract would justify MDL?
Which pinned paired-runtime operator governs actual perturbation recovery?
Which boundary/manifold replacements admit meaningful tangent/normal comparisons?
Can independent recorded measurements falsify the synthetic stability result
without leaking held-out observations into calibration? These remain open.
