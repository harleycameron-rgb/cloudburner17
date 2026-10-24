import asyncio
import json
import os
import shutil
import sys
import time
from contextlib import asynccontextmanager

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
if not os.path.isdir(SRC_DIR):
    SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.append(SRC_DIR)

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

if __package__:
    from .scandoc_page import router as scandoc_router
else:
    from scandoc_page import router as scandoc_router

from admission import evaluate_submission
from supervisor import Supervisor
from ignite import ignite
from burn_harness import burn_harness
from residue import Residue
from tentacled_sphere import TentacledSphere

sup = None
SPHERICAL_BRIDGE = os.path.join(SRC_DIR, "spherical_runtime_bridge.mjs")
SPHERICAL_INPUT_LIMIT = 1024 * 1024


@asynccontextmanager
async def lifespan(app):
    global sup
    sup = Supervisor()
    sup.add_step(
        "burn",
        action=lambda: burn_harness([1, 2, 3], [0.5, 0.7], [0, 1, 2]),
        verify=lambda out: "lambda_updated" in out,
    )
    sup.add_step(
        "ignite",
        action=lambda: ignite([1, 2, 3], [0.5, 0.7], [0, 1, 2]),
        verify=lambda out: "InvariantEngine" in out,
    )
    sup.add_step(
        "residue",
        action=lambda: Residue([1.0, 2.0, 3.0], "mapping-definition"),
        verify=lambda out: isinstance(out[0], float),
    )
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(scandoc_router)


@app.get("/runtime")
async def runtime_stub():
    return {
        "status": "ok",
        "timestamp": time.time(),
    }


@app.get("/tentacled-sphere")
async def tentacled_sphere(seed: float = 1.0, delta: float = 0.1137):
    try:
        return TentacledSphere(seed=seed, delta=delta).actuate()
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.get("/", response_class=HTMLResponse)
def frontend():
    return """<!doctype html>
<html><head><meta charset="utf-8"><title>CLOUDBURNER17</title></head>
<body><h1>CLOUDBURNER17 Supervisor</h1>
<nav aria-label="Main navigation"><a href="/tentacle-sphere">Tentacle Sphere</a></nav>
<button onclick="run('burn')">Burn</button>
<button onclick="run('ignite')">Ignite</button>
<button onclick="run('residue')">Residue</button>
<h2>Live admission check</h2>
<textarea id="admission" rows="14" cols="80">{"candidate":{"name":"live-submission","preserves_curvature":true},"cycle":[{"kappa":0,"rho":0,"kappa_p":1,"kappa_s":1,"observed":true,"curvature_continuous":true,"manifold_before":{"nodes":[1,2]},"manifold_after":{"nodes":[1,2]},"flow_before":[1,2],"flow_after":[1,2]}],"massless_states":[{"kappa":0,"rho":0,"observed":true}]}</textarea>
<button onclick="checkAdmission()">Check admission</button>
<h2>Spherical runtime</h2>
<p>Local verification only; this does not submit a signature or Bitcoin anchor.</p>
<label for="spherical-scenes">Scenes</label>
<textarea id="spherical-scenes" rows="8" cols="80">[{"id":"origin-module","content":"declared origin topology","layer":0},{"id":"shell-module","content":"declared shell topology","layer":1,"dependencies":["origin-module"]}]</textarea>
<label for="spherical-shifts">Optional shifts</label>
<textarea id="spherical-shifts" rows="3" cols="80">[{"id":"sphere-shift-1","twistRadians":0.5235987755982988}]</textarea>
<button onclick="runSpherical()">Run spherical runtime</button>
<pre id="output"></pre>
<script>
async function run(step) {
  const response = await fetch(`/supervise/${step}/y`, {method: "POST"});
  document.getElementById("output").textContent = JSON.stringify(await response.json());
}
async function checkAdmission() {
  const response = await fetch("/admission", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: document.getElementById("admission").value
  });
  document.getElementById("output").textContent = JSON.stringify(await response.json());
}
async function runSpherical() {
  try {
    const response = await fetch("/spherical/ignite", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        scenes: JSON.parse(document.getElementById("spherical-scenes").value),
        shifts: JSON.parse(document.getElementById("spherical-shifts").value)
      })
    });
    document.getElementById("output").textContent =
      JSON.stringify(await response.json(), null, 2);
  } catch (error) {
    document.getElementById("output").textContent = String(error);
  }
}
</script></body></html>"""


@app.get("/tentacle-sphere", response_class=HTMLResponse)
@app.get("/tentacle-sphere/", response_class=HTMLResponse, include_in_schema=False)
def tentacle_sphere_page():
    return HTMLResponse("""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Tentacle Sphere — CLOUDBURNER17</title>
  <style>
    body { margin: 0; color: #111; background: #fff; line-height: 1.6; }
    main { max-width: 48rem; margin: auto; padding: clamp(1rem, 4vw, 3rem); }
    h1 { line-height: 1.2; overflow-wrap: anywhere; }
    a { color: #0000ee; }
    a:focus-visible { outline: 3px solid #111; outline-offset: 4px; }
    figure { margin: 2rem 0; padding: clamp(1rem, 4vw, 2rem);
             border: 2px dashed #666; text-align: center; }
    figcaption { font-weight: bold; }
  </style>
</head>
<body>
  <main>
    <nav aria-label="Page navigation"><a href="/">Return to home</a></nav>
    <h1>Tentacle Sphere</h1>
    <p>An introduction to the idea of a sphere with extending tentacles,
       and a space reserved for a future visualization.</p>
    <p>This initial page is informational only. No simulation or live
       integration is connected.</p>
    <figure aria-labelledby="visualization-label">
      <figcaption id="visualization-label">Visualization placeholder</figcaption>
      <p>No visualization is running. This area is reserved for future work.</p>
    </figure>
    <p>This page does not submit samples, perform admission checks, burn
       receipts, save data, or run agent actions.</p>
  </main>
</body>
</html>""", headers={
        "Content-Security-Policy": (
            "default-src 'none'; style-src 'unsafe-inline'; connect-src 'none'; "
            "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
        ),
        "X-Content-Type-Options": "nosniff",
    })


@app.post("/supervise/{step}/{decision}")
async def supervise(step: str, decision: str):
    try:
        result = sup.run(step, decision)
    except Exception:
        return {"status": "failed", "step": step}
    if result.get("status") in {"completed", "skipped"}:
        return {"status": result["status"], "step": step}
    return {"status": "failed", "step": step}


@app.post("/admission")
async def admission(payload: dict):
    try:
        return evaluate_submission(payload)
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/spherical/ignite")
async def spherical_ignite(payload: dict):
    try:
        encoded = json.dumps(
            payload, allow_nan=False, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=422, detail="Invalid JSON values") from error
    if len(encoded) > SPHERICAL_INPUT_LIMIT:
        raise HTTPException(status_code=413, detail="Request exceeds the 1 MiB limit")
    if (not isinstance(payload.get("scenes"), list) or
            not payload["scenes"] or len(payload["scenes"]) > 512):
        raise HTTPException(
            status_code=422, detail="scenes must contain between 1 and 512 entries"
        )

    node = shutil.which(os.environ.get("NODE_BINARY", "node"))
    if not node:
        raise HTTPException(status_code=503, detail="Node.js runtime is unavailable")

    try:
        process = await asyncio.create_subprocess_exec(
            node,
            SPHERICAL_BRIDGE,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except OSError as error:
        raise HTTPException(status_code=503, detail="Node.js runtime is unavailable") from error

    try:
        stdout, _ = await asyncio.wait_for(
            process.communicate(encoded), timeout=15
        )
    except asyncio.TimeoutError as error:
        process.kill()
        await process.communicate()
        raise HTTPException(status_code=504, detail="Spherical runtime timed out") from error

    try:
        result = json.loads(stdout)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HTTPException(
            status_code=502, detail="Spherical runtime returned an invalid response"
        ) from error

    if process.returncode:
        error_code = result.get("error") if isinstance(result, dict) else None
        if error_code == "invalid_request":
            raise HTTPException(status_code=422, detail="Invalid spherical request")
        if error_code == "runtime_unavailable":
            raise HTTPException(
                status_code=503, detail="Spherical runtime modules are unavailable"
            )
        raise HTTPException(status_code=500, detail="Spherical runtime failed")
    return result
