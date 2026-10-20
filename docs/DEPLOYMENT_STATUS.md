# Deployment status

## CI and manual deployment preparation — 2026-10-20

This section supersedes historical deployment instructions below. **Deployment
is disabled by default.** No deployment, promotion, rollback, secret retrieval or
change, access-control/DNS change, infrastructure provisioning, live ignition,
Sphere write, or AI transmission was initiated by this implementation.
All existing live/qualification gates remain closed. Offline unit tests exercise
synthetic in-memory lifecycle mathematics, not physical operations.

### What actually builds and runs

- Root `package.json`: ES modules, Node **>=18**, no dependencies, no lockfile,
  no `build`/`lint` script. CI uses Node **22** because the existing
  `test:typescript` script needs native `--experimental-strip-types` (not Node 18
  or 20). `frontend/` and `backend/scandoc/` are plain static assets, not a
  separate npm application. Do not run fictitious `npm ci` or `npm run build`.
- Root `pyproject.toml`: Python **>=3.11**, `fastapi`/`uvicorn`, and current
  Vercel entrypoint **`backend.main:app`**. Backend requirements declare the same
  dependency pair. CI tests zero-data behavior on **3.11 and 3.12**, with backend
  pytest on 3.12. Existing pytest files were previously absent from CI discovery.
- `backend/constraints-ci.txt` is the actual `pip freeze` result from a fresh
  Python 3.12 virtualenv after installing backend requirements, the existing
  council dependency `httpx==0.28.1`, and `pytest==8.3.5` for existing pytest tests.
  It pins resolved versions for CI and the existing Docker build. It is **not**
  a fabricated ecosystem lockfile or a hash/platform lock. No npm lock was
  generated for the dependency-free manifest.
- Docker is the real backend build: `backend/Dockerfile` uses Python 3.11-slim,
  installs Node with an enforced >=18 floor, and disables bytecode/access logs.
  The base tag and apt repository remain mutable; builds are not bit-for-bit
  reproducible. Vercel independently resolves `pyproject.toml`; its runtime and
  dependency parity must be reviewed before enabling deployment.

### CI topology and exact commands

`.github/workflows/cloudburner17.yml` runs for main pushes, PRs targeting main,
and `workflow_dispatch`. It calls the existing container, zero-data and council
workflows as reusable workflows, without path filters or duplicate event runs.
The terminal **Required CI** job fails on any failed, skipped or cancelled
dependency. Configure that check as required in main's ruleset/branch protection;
do not use the ambiguous `Vercel – cloudburner17` status as a CI gate.
Every action is pinned to a verified commit SHA, permissions are `contents: read`,
checkout does not persist credentials, and every executable job has a timeout.
CI cancels superseded runs; deployments serialize per environment and are not
cancelled by later CI pushes. No application secrets are supplied to CI.

From `/home/runner/work/cloudburner17/cloudburner17`, the checks are:

```sh
npm install --ignore-scripts --package-lock=false --no-audit --no-fund
npm test
npm run test:typescript
node --check frontend/app.js
node --check backend/scandoc/app.js
node --check backend/scandoc/model.js

python -m pip install --disable-pip-version-check \
  -c backend/constraints-ci.txt -r backend/requirements.txt httpx pytest
python -m pip check
PYTHONDONTWRITEBYTECODE=1 OPENROUTER_API_KEY= python -B -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 OPENROUTER_API_KEY= python -B -m pytest \
  -p no:cacheprovider backend/tests tests/test_ci_deployment.py

docker build --progress=plain -f backend/Dockerfile -t cloudburner17:ci .
docker run --rm --entrypoint node cloudburner17:ci --input-type=commonjs \
  -e 'console.log(process.versions.node); if (Number(process.versions.node.split(".")[0]) < 18) process.exit(1);'
```

The zero-data workflow retains its supervised numerical pipeline, autonomous
sentinel self-verification and package-module entrypoint checks unchanged.
The separate seven-test council check retains socket connection denial and
mocked model calls; it now runs on every CI invocation. Never supply an
OpenRouter key or invoke actual inference for these checks.

The container workflow starts only an ephemeral loopback-bound container,
waits for GET `/runtime`, and runs:

```sh
python -B .github/scripts/vercel_checks.py smoke http://127.0.0.1:18000
```

It stops the container on exit. The old POST `/supervise/burn/y` smoke is
deliberately replaced: smoke checks must not execute lifecycle operations.
Allowlisted GETs are `/`, `/runtime`, `/scandoc`, `/scandoc/app.js`,
`/scandoc/model.js`, `/scandoc/style.css`; source inspection and local container
checks verify these are read-only. They check HTML identity, runtime JSON,
SCANDOC CSP, asset media/security headers and exact tested asset bytes.
They do not click controls, execute browser scripts, request `/tentacled-sphere`,
or call any POST route. They do not establish full backend/spherical correctness.

Artifacts (7-day retention) contain only JavaScript/zero-data test output,
backend JUnit XML, container build output and deployment status/smoke summaries.
They never upload `.vercel/`, `.env`, build function bundles, dependency
directories, credentials, request/response bodies, or application data.
Shell pipeline failures propagate through `pipefail`; no check uses
`continue-on-error`. Dependency installation, configuration failures and failed
tests remain visible.

### Required owner configuration and approvals — not performed

1. Resolve the **existing failing configuration contract**:
   `backend/tests/test_preview_config.py:15` requires
   `backend.scandoc_page:app`, while the actual manifest selects
   `backend.main:app`. Do not weaken the test simply to deploy. An owner must
   decide and separately review which application is authorized. The native app
   exposes supervisor/admission/spherical POST routes; deployment protection is
   not a substitute for reviewing that surface. If the standalone app is chosen,
   update the smoke expectations in the same reviewed change.
2. Verify the existing intended **Vercel** team/project
   **waxtablet/waxtabletproject**, project
   `prj_NqPa3tWgpxJ5uuZX9OCFnhwHtvd4`, team
   `team_FvvGW28W3COeiV8AqQKY3ZA3`. This is a Vercel target, not an assumed
   GitHub repository name. Confirm GitHub source
   `harleycameron-rgb/cloudburner17`, repository-root build directory, framework,
   supported Python/Node runtime, protection and environment settings.
   The preflight performs a read-only Vercel project API check of exact
   ID/team/name/root and Git source before any `pull`/build/deploy.
   A mismatch **fails**; it never links, creates or substitutes a project.
3. **External integration blocker:** PR #45's existing Vercel bot comment
   <https://github.com/harleycameron-rgb/cloudburner17/pull/45#issuecomment-6302461383>
   reports READY at 2026-10-20 21:52 UTC for a *different* project,
   `prj_WZlBVbIMYdypNKKVvfhr7HFzwHA9`, `scandoc-sphere/cloudburner17`,
   rooted at `backend`. The matching GitHub status points there too.
   This is evidence of Git-triggered deployment outside this pipeline, **not**
   verification of the intended mapping, accessibility or application runtime.
   Owners must disable automatic Git deployments on **all** projects connected
   to this source (preview and production), retire duplicate deployment hooks
   or other deployment automation, and confirm the Actions-only path.
   Do not disable authentication or create another project. These external
   settings were not changed here; until changed, even PR pushes may trigger
   the existing integration independently of CI. No workflow can retroactively
   prevent that. Do not enable this deployment path while that risk remains.
4. Create GitHub environments named **preview** and **production**. Require
   independent reviewers, prevent self-review/admin bypass where supported,
   restrict deployment branches to **main**, and require explicit approval for
   each deployment. If the repository plan cannot enforce these protections,
   keep deployment disabled. Set main's required CI protection separately.
5. Configure only the following **names**, in each protected environment:
   - Secret: `VERCEL_TOKEN` (least-scope token authorized for the existing team).
   - Variables: `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` (the exact IDs above).
   - Variable: `VERCEL_GIT_INTEGRATION_DISABLED=true` **only after** step 3 is
     independently verified; this is an operator attestation, not an API-proven
     property of GitHub Actions.
   - Variable: `VERCEL_DEPLOY_ENABLED=true` **only after** all blockers and
     reviews are resolved. Missing/false values fail an opted-in run.
   No bypass token, OpenRouter key, Sphere credentials, or live-control
   configuration is required. No credential values were requested or inspected.

### Future authorized deployment procedure — not executed

Keep the default dispatch input **deployment=none**. Neither PRs nor pushes
can deploy. Both deployment jobs require successful CI **in that same run**,
`workflow_dispatch` on **main**, opt-in `preview` or `production`, the matching
protected environment approval, and successful preflight. Dispatch only from
main; other refs are CI-only. Initially authorize preview only; leave production's
enable variable unset. Never enable automatic production deployment.

After separate authorization, select *CLOUDBURNER17 Pipeline → Run workflow*,
branch main, deployment preview; inspect the selected commit and all CI checks,
then approve the preview environment. The pinned `vercel@64.7.0` client runs:

```sh
# Run by the protected workflow, not commands to execute during PR review.
python -B .github/scripts/vercel_checks.py verify
vercel pull --yes --environment=preview --token="$VERCEL_TOKEN"
vercel build --token="$VERCEL_TOKEN"
vercel deploy --prebuilt --yes --token="$VERCEL_TOKEN"
```

The workflow uses the verified `VERCEL_ORG_ID`/`VERCEL_PROJECT_ID`, never an
interactive project-creation flow. `pull` retrieves deployment configuration
only inside the approved job; never print/upload the resulting `.vercel`
directory or environment files. For a separately approved **production**
dispatch, pull uses `--environment=production`; both build and deploy add
`--prod`. Production deployment can move production aliases; it requires its
own approval and is not a preview promotion. These CLI build/deploy paths are
prepared, **not live-tested** here.

After CLI success, an authenticated **read-only** API check must confirm
the returned deployment's project, target and `readyState=READY`.
The separate **unauthenticated**, GET-only smoke step then checks the returned
HTTPS `*.vercel.app` URL, with redirects disabled and no credential headers.
READY means deployment processing completed, **not public accessibility or
runtime correctness**. HTTP 401/403 means protected/inaccessible to this check;
redirects (including login redirects), unexpected bodies, missing Node-backed
routes, or invalid responses fail visibly. Stop and record the blocker; never
bypass or relax protection to make a smoke check green. Protected applications
may require a separately authorized human read-only check; no such check is
claimed here. Even a passing smoke does not qualify live operations.

### Rollback procedure — not executed

Before any authorized production run, record the existing project's previous
known-good production deployment ID/URL and commit in the approved change
record. If build/deploy fails, stop and inspect; do not retry into a different
project. If deployment reaches READY but smoke fails, it may already be active:
failure is **not automatic rollback**. Keep all live gates closed, notify the
environment approver, and have an authorized owner use the existing project's
Vercel **Instant Rollback** to that recorded deployment after verifying project,
team and target. Do not change DNS, protection or create infrastructure.
Run the same read-only READY/accessibility checks afterward; authentication
blocks remain blocks. For previews, do not promote the failed preview; use the
previous verified preview URL and investigate. Source rollback is a reviewed
revert PR through Required CI, followed by a new manually approved deployment,
not an unreviewed redeploy or an automatic production push.

### Implementation evidence and unresolved outcomes

Local environment: Node 22.23.3, npm 10.9.9, Python 3.12.3, Docker 28.0.4.
Dependency advisory checks found no reported vulnerabilities in the added
version pins/actions/client. `actionlint` 1.7.7 (including ShellCheck) validated
all workflows after fixing one unused loop variable.

- Manifest npm installation, served-JS syntax checks: exit 0.
- Focused SCANDOC/page tests: **9 passed**, exit 0.
- Full `npm test`: **91 passed**, exit 0.
- `npm run test:typescript`: **4 passed**, exit 0.
- Final Python 3.12 unittest discovery: **91 passed**, exit 0.
- Final backend plus deployment guard pytest run: **14 passed, 1 failed**,
  exit 1. The failure is the unchanged entrypoint conflict described above,
  not an ignored/expected-success result.
- Final focused deployment guard tests: **6 passed**, exit 0.
- Hosted Python **3.11.17** unittest discovery with the same constraints:
  **91 passed**, exit 0 (includes the additional READY guard test).
- Exact council workflow command with socket connections denied: **7 passed**,
  exit 0; no external model call.
- Docker build: exit 0; image Node **20.19.2** satisfies >=18.
  Six loopback GET/content/header checks: exit 0; ephemeral container stopped.
- An additional unittest run *inside the slim container* had **88 passed,
  3 failed**, exit 1: lazy dependency-import tests count denied reads of absent
  standard-library `__pycache__` paths. Diagnostic audit observation confirmed
  these missing cache reads, not a dependency resolution failure. The guard
  was not relaxed. This image-specific limitation remains; it is not a claim
  of complete container runtime correctness. The Actions-hosted Python 3.11
  suite and container's read-only smoke passed independently.
- The supervised executable/module commands were preserved, not separately
  invoked as a live operation. No Vercel CLI build/deploy, API credential check,
  protected external smoke, promotion or rollback was run.
- Recent main workflows were successful; initial PR Actions runs
  `39503757014` and `39503756811` were **action_required**, zero executed jobs.
  GitHub log lookup found no failed jobs/logs for that pending-approval run;
  that is not a remote CI pass.
- Intended mapping, external integration shutdown, entrypoint authorization,
  Vercel runtime/dependency parity, environment setup, branch protection and
  required reviews remain **owner blockers**. Vercel documentation retrieval
  was unavailable due to DNS, so no remote deployment guarantee is asserted.

## Current PR merge-resolution update — 2026-10-16

No deployment was initiated by this merge-resolution task. Current preview or
deployment status was checked via the GitHub commit status for head
`15dbf25aa488ea98f37baf1197a74658f8d2fa4c`: context `Vercel – cloudburner17`
reported **success**, “Deployment has completed,” at 2026-10-16 18:15:58 UTC.
This is consistent with an automatic preview; no deployment was initiated or
promoted by this task. The status target is a Vercel project page; the preview
URL and application response were not independently tested, so runtime behavior
remains unverified. No live action, physical control, DNS change, or persistent
write was initiated. The hash1536 readiness contract continues to require
`liveGate: "CLOSED"` and unresolved, unauthorized qualification. No deployment
or privacy qualification is asserted.

This status observation is for the cited head; the subsequent evidence-only
branch update was not part of that status check and may independently trigger
an automatic preview.

The following records the separate historical main-branch synthetic preview
repair workstream; its observed deployment status must not be confused with
the status of this PR's current head.

## Historical main workstream: standalone synthetic preview repair

### Provenance and scope (2026-10-16)

- Requested inspected baseline: `319a7df1283b6a266a8a9ce6ddd7f42e405c55b9`.
- Actual initial checkout: `58251d51b1e917ec4722af533ee6063bafa1ba3d`.
  Initial worktree was clean; no unrelated changes were overwritten.
- Existing Vercel project: `prj_BvHWk06AfoyC9qsuqaLwg4VHj5ib`, team
  `team_FvvGW28W3COeiV8AqQKY3ZA3`, framework `fastapi`.
- The supplied deployment `dpl_xt3JgY8E4FD1H75V1nE6shvz5vdZ` failed with
  `FASTAPI_ENTRYPOINT_NOT_FOUND` according to the issue's build evidence.
  These historical Vercel logs were not independently retrieved here.
- PR #37's initial Vercel bot comment independently reports **Error** at
  <https://vercel.com/waxtablet/cloudburner17/5D9o3fd5cNUVA6J5qmCTFjHRRTQe>,
  updated 2026-10-16 13:40:31 UTC, with no preview URL and rootDirectory null.

Root `pyproject.toml` explicitly selects **`backend.scandoc_page:app`**.
Its `[project]` metadata declares the same `fastapi` and `uvicorn` dependencies
as the unchanged backend requirements; root `vercel.json` explicitly includes
`backend/scandoc/**` (index.html, app.js,
model.js, style.css). There is no replacement animation, runtime adapter, or
geometry change. The standalone app now redirects `/` to `/scandoc`; the
native app's root is unchanged. All four existing assets remain preloaded.

Deploy from the **repository root** using the existing Git-linked protected
preview only. Do not deploy using `backend/vercel.json`: that existing
backend-root configuration falls through to `main.py`, which exposes
unauthenticated supervisor/admission/spherical POST routes. Neither
`backend/main.py`, `backend/server.py`, native sources, nor that legacy
configuration was changed. Public native hosting requires separately reviewed
access controls.

Local standalone command:

```sh
cd /home/runner/work/cloudburner17/cloudburner17
PYTHONDONTWRITEBYTECODE=1 python -B -m uvicorn backend.scandoc_page:app \
  --host 127.0.0.1 --port 18002 --no-access-log
```

This is a **standalone synthetic sandbox**, not an integration of the original
six-leg prototype, daemon, six applications, time axis, or live systems.
Passing existing paired-geometry tests does not demonstrate those integrations.
The preview has no lifecycle or council routes. Its page CSP forbids connections;
it is not a claim about the native runtime's zero-data audit guarantees.

## Council limitations — unchanged user-supplied module

`src/multi_llm_council.py` is not integrated into the backend API or sandbox.
It contains an outbound OpenRouter client, but this PR never calls it:
the seven committed tests import the actual module with real `httpx` installed
and mock `call_model`, with socket connections additionally denied.

- If invoked with credentials, the module transmits prompts/replies externally.
  In-memory local handling is **not proof of provider zero retention**.
- `rounds` is accepted but unused; only one collection round and a chairman
  synthesis are implemented (`run_council`, lines 130–200).
- Sentinel verification must copy the serialized result and blank its
  `sentinel` field before hashing, as the existing tests do. Hashing the final
  dictionary including its populated sentinel is not the same calculation.
- Provider/model availability, actual multi-model inference, retention policy,
  and end-to-end API integration were not tested or established.

## Verification and remaining blockers

Local configuration import, 14 real loopback HTTP GET checks, and targeted/full
regressions passed; see [TEST_EVIDENCE.md](TEST_EVIDENCE.md). This is local
evidence, **not an externally verified deployment**.

At this checkpoint, no repaired Git-linked preview has been observed yet.
Do not interpret a later READY status as externally verified without GET checks
for `/`, `/scandoc`, both JS modules, and CSS. If protection requires
authentication, record the response and stop; do not bypass it.

GitHub zero-data workflow run `38909665697` failed at the initial checkout:
`ModuleNotFoundError: No module named 'httpx'`; 52 discovered items, one import
error, exit 1. That workflow does not install the council dependency. The
separate council workflow installs `httpx==0.28.1`, but its path filter does
not select this packaging-only repair. This pre-existing CI dependency gap is
recorded, not silently repaired in this bounded deployment change.

Next blocker: observe a successful build of this repair in the existing
protected preview, then obtain authorized external GET smoke evidence.
Complete daemon/six-app/time-axis integration and actual multi-model inference
remain separate work. No project creation, protection changes, credentials,
DNS changes, promotion, merge, live launch/burn/shift/supervision, council
requests, or paid infrastructure expansion were performed.

## Post-push evidence

First repair attempt: `d0bf92a6f7d7c56343aac08561fa0b47e09ab765`.
The subsequent manifest correction below supersedes its packaging.

At 2026-10-16 13:46:43 UTC, GitHub's commit status for the **requested**
project reported **failure** for `dpl_3sGQLubZ3sJCjPGUVwCGu6sKrU58`:
<https://vercel.com/waxtablet/cloudburner17/3sGQLubZ3sJCjPGUVwCGu6sKrU58>.
The status recommends `npx vercel inspect ... --logs`, but no Vercel CLI or
authenticated Vercel tooling is available. Read-only dashboard retrieval failed
DNS resolution; browser tooling returned `Transport closed`. A credential-free
GET to the deployment events API also failed DNS (curl exit 6, HTTP 000).
Consequently the **new build failure's cause is unknown**; it must not be
assumed to be the historical entrypoint error or described as repaired remotely.

At 13:46:48 UTC the Vercel bot replaced its table with a READY deployment in
**another** existing project, `prj_WZlBVbIMYdypNKKVvfhr7HFzwHA9`, under
`scandoc-sphere`, rooted at **backend**:
<https://vercel.com/scandoc-sphere/cloudburner17/5y7TGc8t6HXXVeVQEQkfUHTS8dvu>.
It advertises
<https://cloudburner17-git-copilot-create-bounded-02f35d-scandoc-sphere.vercel.app>.
This deployment does not exercise the repaired root configuration and uses the
unchanged legacy routing. It was **not** used as a substitute preview or smoke
tested; protection and runtime behavior are unverified. No project was created
or modified by this agent.

Thus there is **no externally verified first working synthetic preview**.
The immediate next blocker is authorized build-log access for the requested
project's failed Git-linked deployment, followed by a successful protected
preview build and authorized GET smoke checks. No production action is needed.

CodeQL reported **zero Python alerts**. The parallel code-review service could
not initialize its configured model; its “no comments” output is not a completed
review. A separate read-only review was requested as a fallback.
Repair-commit Actions runs `38910481846` (backend) and `38910482007`
(zero-data) were observed as `action_required`, not passing test runs.

### Review-driven manifest correction

The fallback reviewer identified that Vercel prioritizes `pyproject.toml` and
runs `uv lock`: a tool-only TOML plus delegated requirements was insufficient.
Added valid project name/version/Python compatibility and the existing backend
dependency pair to the root manifest; removed the redundant root requirements
file. This addresses a concrete local packaging defect, but is not proof of
the earlier remote failure's cause without its logs.

`uv 0.13.1` validated the corrected project using `uv lock --dry-run`:
15 packages resolved, exit 0, no repository lockfile or environment created.
The nine backend/configuration tests passed again with socket connections
blocked (exit 0). Full command evidence is in TEST_EVIDENCE.md.

### Corrected code checkpoint

Corrected tested code commit: **`e2b321ca88e6588f91f75a81e26bf778ddcf2fd4`**.
The fallback reviewer rechecked the correction and reported no significant
issues. Parallel validation was rerun: zero CodeQL Python alerts; its separate
review subprocess still could not initialize its configured model.

At 13:51:28 UTC the requested project's GitHub status was **pending**,
“Vercel is deploying your app”, for
<https://vercel.com/waxtablet/cloudburner17/6PH8es2oLeSJtuz167E2VBzfZrNc>.
At 13:51:39 UTC the identically named status context instead showed success
for the **other backend-root project**, deployment
`6EbqhUzpbsxfn49JuBpctXZjDDQg`; its bot table was updated at 13:51:42 UTC.
That overwrites the visible combined status, so the requested project's
corrected build outcome is **unknown**, not proven failed or successful.
Unauthenticated GitHub status-history retrieval returned HTTP 403 (curl exit 22).
No requested-project preview URL or authorized external runtime response was
obtained. The other project's READY preview remains unverified and is not a
substitute for the requested project.

Corrected-commit Actions runs `38911106138` (backend) and `38911106426`
(zero-data) require approval (`action_required`). The pre-existing missing
httpx CI issue remains a known separate blocker. Stop at this tested PR:
next obtain the corrected requested-project build outcome/logs and an authorized
protected-preview GET smoke. Do not promote, merge, or run live operations.
