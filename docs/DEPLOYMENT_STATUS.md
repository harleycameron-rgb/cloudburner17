# Deployment status

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
