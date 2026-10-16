# Repair test evidence — 2026-10-16

Working directory for every repository command:
`/home/runner/work/cloudburner17/cloudburner17`.
Initial SHA: `58251d51b1e917ec4722af533ee6063bafa1ba3d`;
requested baseline: `319a7df1283b6a266a8a9ce6ddd7f42e405c55b9`.
No native or council source was edited.

## Environment and preparation

Python 3.12.3; Node v22.23.3; pip 24.0; pytest 9.1.1; FastAPI 0.143.2;
Uvicorn 0.54.0; httpx 0.28.1; Starlette 1.8.0; Pydantic 2.14.1;
AnyIO 4.15.1; httpcore 1.0.9; h11 0.16.0.

```sh
python -m pip install --disable-pip-version-check 'fastapi==0.143.2' 'uvicorn==0.54.0' 'httpx==0.28.1' 'pytest==9.1.1'
python -m pip install --disable-pip-version-check -r /home/runner/work/cloudburner17/cloudburner17/requirements.txt
```

Both installs succeeded (exit 0); the second resolved the existing two backend
dependencies through the new root requirements. Advisory checks for the four
explicit versions found no vulnerabilities. Existing unpinned backend
requirements were preserved; deployed dependency resolution may differ.

`unshare -Urn true` failed, exit 1:
`unshare: write failed /proc/self/uid_map: Operation not permitted`.
Thus isolation below is the **committed workflow's Python socket patch**,
not OS-level network isolation. Shell test subprocesses do not inherit Python
patches; audited existing subprocesses use local Python/module/CLI fixtures,
not network clients. No credentials or inference calls were used.

## Side-effect audit

Read the council suite, backend tests, sandbox tests, root Python tests, and
workflows before execution. Council tests mock `call_model`; backend spherical
tests mock process creation; TestClient uses in-process ASGI without entering
the native app's Supervisor lifespan. Geometry/zero-data tests use local
fixtures and child Python processes. Zero-data hooks are process-global, so
backend, council, and root suites ran in separate processes with bytecode
disabled and pytest caching disabled. Native workflow container POST smoke,
standalone supervised-build invocations, live endpoints and inference were
not run. Existing test-only synthetic lifecycle scenarios are not live actions.

## Commands, counts, and results

### Exact council workflow-equivalent test

```sh
PYTHONDONTWRITEBYTECODE=1 OPENROUTER_API_KEY='' python -B - <<'PY'
import socket
import unittest
from unittest.mock import patch

def deny_network(*args, **kwargs):
    raise AssertionError("Network connections are forbidden in council tests")

with patch.object(socket.socket, "connect", deny_network), \
     patch.object(socket.socket, "connect_ex", deny_network), \
     patch.object(socket, "create_connection", deny_network):
    suite = unittest.defaultTestLoader.discover(
        "tests", pattern="test_multi_llm_council.py"
    )
    if suite.countTestCases() != 7:
        raise AssertionError("Expected exactly seven council tests")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
PY
```

**7/7 passed, 0.002 s, exit 0**. Real `src/multi_llm_council.py` and
`httpx==0.28.1`; no fake replacement module or model inference.

### Backend/configuration tests

```sh
PYTHONDONTWRITEBYTECODE=1 OPENROUTER_API_KEY='' python -B - <<'PY'
import socket
from unittest.mock import patch
import pytest

def deny_network(*args, **kwargs):
    raise AssertionError('Network connections are forbidden in backend tests')

with patch.object(socket.socket, 'connect', deny_network), \
     patch.object(socket.socket, 'connect_ex', deny_network), \
     patch.object(socket, 'create_connection', deny_network):
    raise SystemExit(pytest.main(['-p', 'no:cacheprovider', '-v', 'backend/tests']))
PY
```

Initial run: **8 passed, 1 failed, exit 1**. The added test inspected
`route.methods`, but FastAPI's `_IncludedRouter` lacks that attribute.
Corrected the test to inspect OpenAPI operations, not framework internals.
Same command rerun: **9/9 passed, 0.46 s, exit 0**.
One Starlette warning: httpx-based TestClient is deprecated in this installed
version; no additional HTTP client was added to suppress it.

### Existing sandbox and complete regressions

```sh
node --test tests/scandoc.test.js tests/scandoc_page.test.js
PYTHONDONTWRITEBYTECODE=1 OPENROUTER_API_KEY='' python -B -m unittest discover -s tests -p test_synthetic_geometry.py -v
npm test
```

Respectively: **9/9 passed**, **5/5 passed**, **80/80 passed**; each exit 0.
The full JS run is the existing `node --test tests/*.test.js` workflow command
(local Node 22 rather than workflow Node 20).

Full Python discovery with the same connection-blocking boundary:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENROUTER_API_KEY='' python -B - <<'PY'
import socket
import unittest
from unittest.mock import patch

def deny_network(*args, **kwargs):
    raise AssertionError('Network connections are forbidden in offline tests')

with patch.object(socket.socket, 'connect', deny_network), \
     patch.object(socket.socket, 'connect_ex', deny_network), \
     patch.object(socket, 'create_connection', deny_network):
    suite = unittest.defaultTestLoader.discover('tests')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
PY
```

**58/58 passed, 0.280 s, exit 0**, including the seven council tests. This
matches zero-data workflow test discovery with httpx installed and socket
blocking added; it is not a claim to have run every workflow step.
`git diff --check`: exit 0.

## Real local HTTP smoke

Server command (stdout/stderr captured outside the repository):

```sh
PYTHONDONTWRITEBYTECODE=1 OPENROUTER_API_KEY='' python -B -m uvicorn backend.scandoc_page:app --host 127.0.0.1 --port 18002 --no-access-log
```

A Python `httpx.Client(base_url='http://127.0.0.1:18002', trust_env=False)`
performed the following **14 GET assertions; exit 0**. The server reached
“Application startup complete” and was terminated after the checks.
Before HTTP, `tomllib` parsed the root entrypoint, `importlib.import_module`
loaded it, all four preloaded asset names were asserted, and
`'backend.main' not in sys.modules` passed in a fresh process.

| Request | Observed and asserted result |
| --- | --- |
| `/` | 307, Location `/scandoc` |
| `/scandoc`, `/scandoc/` | 200, `text/html; charset=utf-8`, exact existing CSP |
| `/scandoc/app.js`, `/scandoc/model.js` | 200, `text/javascript; charset=utf-8`, nosniff |
| `/scandoc/style.css` | 200, `text/css; charset=utf-8`, nosniff |
| `/scandoc/main.py`, `/scandoc/index.html`, `/scandoc/missing.js` | 404 |
| `/admission`, `/supervise/burn/y`, `/spherical/ignite`, `/runtime` | 404 |
| `/openapi.json` | 200; exactly three scandoc paths, each GET-only |

Exact page CSP:

```text
default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'none'; img-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'
```

Backend tests additionally assert absent native POST routes (404), sandbox POST
rejection (405), root redirect following, and root bundle/configuration content.
No native live server was started.

## Remote evidence and limits

GitHub MCP inspected workflow runs and logs. Initial-checkout backend container
run `38909665956` passed. Initial-checkout zero-data run `38909665697`,
job `117002386750`, failed with missing `httpx`: 52 discovered items including
one failed import, exit 1. This is not a failure of the seven tests run above
with the dependency installed. Baseline council workflow `38907922933`
succeeded; querying its failed-job logs returned no failed jobs.

External preview evidence is tracked in [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md).
No remote READY/build assertion is treated as a successful external HTTP smoke.
