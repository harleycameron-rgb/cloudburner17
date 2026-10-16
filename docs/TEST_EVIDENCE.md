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
dependencies through the first attempt's root requirements. That file was
subsequently removed in favor of valid root project metadata (see below).
Advisory checks for the four
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

Exact client/import-check command (run while that loopback server was active):

```sh
PYTHONDONTWRITEBYTECODE=1 OPENROUTER_API_KEY='' python -B - <<'PY'
import importlib
import sys
import time
import tomllib
from pathlib import Path
import httpx

root = Path('/home/runner/work/cloudburner17/cloudburner17')
module, name = tomllib.loads((root / 'pyproject.toml').read_text())['tool']['vercel']['entrypoint'].split(':')
app = getattr(importlib.import_module(module), name)
assert 'backend.main' not in sys.modules
assert set(importlib.import_module(module).ASSETS) == {'index.html', 'app.js', 'model.js', 'style.css'}
print('Configured import:', module + ':' + name, '; native backend.main not imported')
with httpx.Client(base_url='http://127.0.0.1:18002', trust_env=False) as client:
    for attempt in range(50):
        try:
            response = client.get('/')
            break
        except httpx.ConnectError:
            time.sleep(0.1)
    else:
        raise AssertionError('Server did not start')
    assert response.status_code == 307 and response.headers['location'] == '/scandoc'
    print('GET / -> 307 /scandoc')
    for path in ('/scandoc', '/scandoc/'):
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers['content-type'].startswith('text/html')
        assert response.headers['content-security-policy'] == importlib.import_module(module).CSP
        print('GET', path, '->', response.status_code, response.headers['content-type'], 'CSP:', response.headers['content-security-policy'])
    for asset, mime in (('app.js', 'text/javascript'), ('model.js', 'text/javascript'), ('style.css', 'text/css')):
        response = client.get('/scandoc/' + asset)
        assert response.status_code == 200 and response.headers['content-type'].split(';')[0] == mime
        assert response.headers['x-content-type-options'] == 'nosniff'
        print('GET /scandoc/' + asset, '->', response.status_code, response.headers['content-type'], 'nosniff')
    for path in ('/scandoc/main.py', '/scandoc/index.html', '/scandoc/missing.js', '/admission', '/supervise/burn/y', '/spherical/ignite', '/runtime'):
        response = client.get(path)
        assert response.status_code == 404
        print('GET', path, '-> 404')
    paths = client.get('/openapi.json').json()['paths']
    assert set(paths) == {'/scandoc', '/scandoc/', '/scandoc/{asset}'}
    assert all(set(methods) == {'get'} for methods in paths.values())
    print('GET /openapi.json -> 200; only three read-only scandoc paths')
print('14 local HTTP GET checks passed')
PY
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

After pushing tested code commit `d0bf92a6f7d7c56343aac08561fa0b47e09ab765`,
the requested project reported deployment `dpl_3sGQLubZ3sJCjPGUVwCGu6sKrU58`
failed. Build logs could not be retrieved via the available read-only paths:

```sh
curl --silent --show-error --max-time 20 --output /tmp/cloudburner17-vercel-events-response.txt --write-out 'HTTP_STATUS=%{http_code}\n' 'https://api.vercel.com/v2/deployments/dpl_3sGQLubZ3sJCjPGUVwCGu6sKrU58/events?teamId=team_FvvGW28W3COeiV8AqQKY3ZA3'
```

**Exit 6, HTTP 000**, `Could not resolve host: api.vercel.com`. Dashboard
web fetch also failed DNS; browser failed with `Transport closed`. No new
credentials, CLI dependency, protection bypass or deployment was attempted.
An unrelated backend-root project's READY bot status is recorded separately,
not considered runtime smoke or evidence that this repair built successfully.

Secret scan: no secrets detected in all nine changed/created files.
Parallel validation: CodeQL Python **0 alerts**. Its code-review subprocess
failed to initialize an unavailable model, so no successful review is claimed
from that subprocess. This tooling failure is distinct from a code finding.

## Review-driven packaging correction

The fallback read-only review found that Vercel chooses `pyproject.toml`
before requirements and invokes `uv lock`. The first tool-only manifest was
therefore incomplete despite passing import tests. Added `[project]` metadata
and `dependencies = ["fastapi", "uvicorn"]`, matching backend requirements,
and removed the now-redundant root requirements file.

```sh
python -m pip install --disable-pip-version-check 'uv==0.13.1'
python -m uv --version
python -m uv lock --dry-run --python /usr/bin/python3 --no-python-downloads --cache-dir /tmp/cloudburner17-uv-cache
```

All exit 0; uv version **0.13.1**, CPython **3.12.3**.
Advisory check for this necessary packaging validator: no vulnerabilities.
The lock dry-run resolved **15 packages** in 258 ms: annotated-doc 0.0.5,
annotated-types 0.8.0, anyio 4.15.1, click 8.5.0,
cloudburner17-preview 0.0.0, fastapi 0.143.2, h11 0.16.0, idna 3.20,
opentelemetry-api 1.45.1, pydantic 2.14.1, pydantic-core 2.50.1,
starlette 1.8.0, typing-extensions 4.16.0, typing-inspection 0.4.4,
uvicorn 0.54.0. No uv.lock or .venv was created in the repository.
This command accesses the package index for dependency metadata; it is not
an inference call or a network-blocked test.

The exact backend socket-blocked command above was rerun against the corrected
manifest and updated dependency-parity assertion: **9/9 passed, 0.44 s,
exit 0**, with the same single TestClient deprecation warning.
The HTTP handler, four assets, native runtime and council module were not
changed by this correction.
