import sys
import os
sys.path.append(os.path.abspath("../src"))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from supervisor import Supervisor
from ignite import ignite
from burn_harness import burn_harness
from residue import Residue

app = FastAPI()
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")

sup = Supervisor()

sup.add_step(
    "burn",
    action=lambda: burn_harness([1,2,3],[0.5,0.7],[0,1,2]),
    verify=lambda out: "lambda_updated" in out
)

sup.add_step(
    "ignite",
    action=lambda: ignite([1,2,3],[0.5,0.7],[0,1,2]),
    verify=lambda out: "InvariantEngine" in out
)

sup.add_step(
    "residue",
    action=lambda: Residue([1.0,2.0,3.0],"mapping-definition"),
    verify=lambda out: isinstance(out[0], float)
)

@app.post("/supervise/{step}/{decision}")
def supervise(step: str, decision: str):
    try:
        result = sup.run(step, decision)
    except Exception:
        return {"status": "failed", "step": step}
    if result.get("status") in {"completed", "skipped"}:
        return {"status": result["status"], "step": step}
    return {"status": "failed", "step": step}
