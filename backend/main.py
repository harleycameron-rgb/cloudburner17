import sys
import os
from contextlib import asynccontextmanager

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from admission import evaluate_submission
from supervisor import Supervisor
from ignite import ignite
from burn_harness import burn_harness
from residue import Residue

sup = None


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

@app.get("/", response_class=HTMLResponse)
def frontend():
    return """<!doctype html>
<html><head><meta charset="utf-8"><title>CLOUDBURNER17</title></head>
<body><h1>CLOUDBURNER17 Supervisor</h1>
<button onclick="run('burn')">Burn</button>
<button onclick="run('ignite')">Ignite</button>
<button onclick="run('residue')">Residue</button>
<h2>Live admission check</h2>
<textarea id="admission" rows="14" cols="80">{"candidate":{"name":"live-submission","preserves_curvature":true},"cycle":[{"kappa":0,"rho":0,"kappa_p":1,"kappa_s":1,"observed":true,"curvature_continuous":true,"manifold_before":{"nodes":[1,2]},"manifold_after":{"nodes":[1,2]},"flow_before":[1,2],"flow_after":[1,2]}],"massless_states":[{"kappa":0,"rho":0,"observed":true}]}</textarea>
<button onclick="checkAdmission()">Check admission</button>
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
</script></body></html>"""


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
