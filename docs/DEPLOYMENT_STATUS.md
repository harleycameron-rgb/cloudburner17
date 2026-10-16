# Standalone synthetic preview repair

## Provenance and scope (2026-10-16)

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
Root `requirements.txt` delegates to the existing backend requirements; root
`vercel.json` explicitly includes `backend/scandoc/**` (index.html, app.js,
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
