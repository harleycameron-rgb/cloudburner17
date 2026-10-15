# Cloudburner live camera and sound prototype

Imported from `reference/builder-source-import`, source commit
`ba561b9ead8f876903a265c37867b4b8b08ee142`. The runnable files have moved into
the application's backend asset structure; this folder retains provenance and
acceptance notes. No JPEG is referenced or included. Uploaded assets are untouched.

Run the application from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 uvicorn backend.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Open `http://localhost:8000/` and follow **Live feedback**, or visit
`http://localhost:8000/live-feedback` directly (trailing slash also works).
Use Start camera + microphone and grant device permissions. Microphone RMS drives
synthetic camera-frame deformation with six manually controlled load inputs.
There is no speaker playback, recording, upload, AI inference, engine firing,
receipt minting, or authenticated app telemetry integration.
Stop, a hidden tab, page exit or a disconnected device releases the devices.
Pending permission grants and video-playback completions are invalidated on
Stop/hide; a late-granted stream is immediately stopped. Browsers provide no
API to dismiss an outstanding permission prompt. Audio nodes disconnect, the
AudioContext closes, sample buffers are zeroed and both canvases are cleared.
The browser/OS may retain its own permission preference or internal buffers;
the page does not persist them. The microphone connects only to an analyser,
never the audio destination.

## File map and routing

- `backend/live_feedback/{index.html,live.mjs,model.mjs}`: moved prototype;
  live-frame processing and the unchanged six-input/RMS model, no engine imports.
- `backend/live_feedback/model.test.mjs`: the eight original model tests.
- `backend/live_feedback_page.py`: preloads three assets before the zero-data
  guard, serves `/live-feedback[/]` and only the two `.mjs` assets with
  `text/javascript` and `nosniff`; CSP blocks network connections.
- `backend/main.py`: includes the page router and links from the actual `/` UI;
  `frontend/index.html` also links, but is not the backend's root entrypoint.
- `vercel.json`: relocated from `backend/vercel.json` to the repository root;
  keeps SCANDOC and the main fallback, adds an engine-free live-feedback function.
  Explicit source includes preserve sibling `src/` imports, page assets and
  Node ES-module metadata without duplicating engine sources. Requires a future
  approved repository-root deployment context; no production settings changed.
- `tests/live_feedback_page.test.js`: browser-API/DOM-stub lifecycle race tests.
- `backend/tests/test_live_feedback.py`: route/MIME/allowlist/isolation tests,
  guard-active asset serving and isolated source-archive import checks.

The existing Dockerfile already copies `backend/`, `src/` and `package.json`,
so no container packaging change is needed. The Vercel archive tests verify
`admission` comes from the copied `src/` under both Python import styles, not
the development checkout. They do **not** prove a Vercel deployment is healthy.

## Manual browser acceptance (target hardware still required)

1. Use HTTPS or localhost. From `/`, follow the link. Repeat with both page URL
   forms; verify both modules return JavaScript, with no CDN or image requests.
2. Confirm no permission prompt/device indicator until Start. Confirm the six
   sliders are TAP, SURFACE, GAIN, HABITAT, ENGINE, BUSINESS and explicitly manual.
3. Grant camera and microphone. Move in view, speak, and move sliders: frames
   deform and the RMS meter responds; no sound should play from speakers.
4. Stop: video goes black, RMS returns to zero, and browser device indicators
   turn off. Repeat Start/Stop several times; restart should work.
5. Deny permissions. Retry. While permission is pending, Stop, then grant:
   devices must be released without displaying a stale frame. Repeat with
   hide/navigate away, and with Stop/Start before answering the old prompt.
6. Hide the tab, minimize, navigate away/back; there must be no automatic restart.
   Unplug each device/revoke permission during startup and while live; both
   devices must release and frames clear. Verify indicators on each target browser.
7. Inspect Network and browser storage: no media upload, recording, application
   persistence, or requests to ignition, burn, shift, admission or sentinel routes.
   Test local endpoints only; never exercise production actuation as acceptance.

## Remaining gaps and approval boundary

Physical camera/microphone and target-device browser testing have not been run
in this environment. Historical Vercel runtime logs were unavailable; Actions
build success is separate from deployed runtime health. No Vercel build/deploy,
production setting change, merge or approval bypass was performed. Node availability
for the existing spherical endpoint still needs a separately approved runtime check.

This PR targets **`reference/builder-source-import`**. It requires a subsequent
reviewed PR to `main`; it does not merge or deploy that branch.

Still missing: original Orrery/Python reference import, real external telemetry
adapters (no six external apps are invented here), cycle coordinator, cube/sphere
lifecycle hooks, fourth-axis coordination, approved firing and separation-position
sentinel integration. This page does NOT implement these or an AI model.
Camera permission never authorizes engine operations. Synthetic output is not
verified invariant evidence.
