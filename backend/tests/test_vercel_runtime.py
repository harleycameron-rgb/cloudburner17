import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import textwrap

import pytest


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def copy_backend(destination):
    destination.mkdir(parents=True)
    for name in ("main.py", "scandoc_page.py", "integration_page.py", "audit_geometry.py", "trajectory_contract.py"):
        shutil.copy2(BACKEND / name, destination / name)
    shutil.copytree(BACKEND / "scandoc", destination / "scandoc")
    shutil.copytree(BACKEND / "portal", destination / "portal")


def test_missing_runtime_source_fails_closed(tmp_path):
    runtime = tmp_path / "task"
    copy_backend(runtime)
    result = subprocess.run(
        [sys.executable, "-E", "-B", "-c", "import main"],
        cwd=runtime, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode != 0
    assert "ModuleNotFoundError: No module named 'admission'" in result.stderr


@pytest.mark.parametrize("layout", ("backend-root", "repository-root"))
def test_isolated_vercel_startup_and_admission(tmp_path, layout):
    runtime = tmp_path / "task"
    config = json.loads((BACKEND / "vercel.json").read_text())
    assert config["routes"] == [
        {"src": "/scandoc(/.*)?", "dest": "/scandoc_page.py"},
        {"src": "/(.*)", "dest": "/main.py"},
    ]
    if layout == "backend-root":
        build = tmp_path / "build"
        copy_backend(build / "backend")
        shutil.copytree(ROOT / "src", build / "src",
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy2(ROOT / "package.json", build / "package.json")
        main_build = next(item for item in config["builds"]
                          if item["src"] == "main.py")
        assert main_build["config"]["framework"] == "fastapi"
        subprocess.run(main_build["config"]["buildCommand"], shell=True,
                       cwd=build / "backend", check=True)
        shutil.copytree(build / "backend", runtime)
        shutil.rmtree(build)
        entrypoint = "main"
        source = runtime / "src"
    else:
        copy_backend(runtime / "backend")
        shutil.copytree(ROOT / "src", runtime / "src",
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy2(ROOT / "package.json", runtime / "package.json")
        entrypoint = "backend.main"
        source = runtime / "src"

    for path in (ROOT / "src").iterdir():
        if path.is_file():
            assert (source / path.name).read_bytes() == path.read_bytes()
    assert json.loads((runtime / "package.json").read_text())["type"] == "module"
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
                   "OPENROUTER_API_KEY": ""}
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-E", "-B", "-c", textwrap.dedent("""
            import copy
            import importlib
            from pathlib import Path
            import sys
            from unittest.mock import patch

            from fastapi.testclient import TestClient

            module = importlib.import_module(sys.argv[1])
            import admission
            import zero_data

            task = Path.cwd()
            assert Path(admission.__file__).parent == task / "src"
            assert Path(module.SPHERICAL_BRIDGE).is_file()
            assert module.evaluate_submission is admission.evaluate_submission
            assert module.sup is None
            assert not zero_data._installed
            payload = {
                "candidate": {"name": "isolated", "preserves_curvature": True},
                "cycle": [{
                    "kappa": 0, "rho": 0, "kappa_p": 1, "kappa_s": 1,
                    "observed": True, "curvature_continuous": True,
                    "manifold_before": {"nodes": [1, 2]},
                    "manifold_after": {"nodes": [1, 2]},
                    "flow_before": [1, 2], "flow_after": [1, 2],
                }],
                "massless_states": [{"kappa": 0, "rho": 0, "observed": True}],
            }
            assert admission.evaluate_submission(payload)["admitted"]
            invalid = []
            for key, value in (
                ("flow_after", [2, 1]),
                ("manifold_after", {"nodes": [1]}),
                ("kappa_s", 2),
                ("curvature_continuous", False),
            ):
                rejected = copy.deepcopy(payload)
                rejected["cycle"][0][key] = value
                invalid.append(rejected)
            rejected = copy.deepcopy(payload)
            rejected["candidate"]["preserves_curvature"] = False
            invalid.append(rejected)
            rejected = copy.deepcopy(payload)
            rejected["massless_states"][0]["observed"] = False
            invalid.append(rejected)

            with patch.object(module, "burn_harness") as burn, \\
                    patch.object(module, "ignite") as ignite, \\
                    patch.object(module, "Residue") as residue, \\
                    patch.object(module.Supervisor, "run") as run, \\
                    patch.object(module.asyncio, "create_subprocess_exec") as launch:
                with TestClient(module.app) as client:
                    assert zero_data._installed
                    assert set(module.sup.steps) == {"burn", "ignite", "residue"}
                    assert module.sup.state_log == []
                    home = client.get("/")
                    assert home.status_code == 200
                    assert "CLOUDBURNER17 Supervisor" in home.text
                    assert 'href="/tentacle-sphere"' in home.text
                    assert client.get("/tentacle-sphere").status_code == 200
                    assert client.get("/runtime").status_code == 200
                    assert client.get("/scandoc").status_code == 200
                    assert client.get("/scandoc/model.js").status_code == 200
                    assert client.get("/scandoc/main.py").status_code == 404
                    assert client.post("/admission", json=payload).json()["admitted"]
                    for rejected in invalid:
                        assert not admission.evaluate_submission(rejected)["admitted"]
                        response = client.post("/admission", json=rejected)
                        assert response.status_code == 200
                        assert response.json()["admitted"] is False
                    malformed_payloads = [
                        {}, {**payload, "cycle": []},
                        {**payload, "massless_states": []},
                        {**payload, "massless_states": [{"kappa": 1, "rho": 0}]},
                        {**payload, "cycle": [{
                            key: value for key, value in payload["cycle"][0].items()
                            if key != "flow_after"
                        }]},
                    ]
                    for malformed in malformed_payloads:
                        assert client.post("/admission", json=malformed).status_code == 422
                    assert module.sup.state_log == []
                    assert zero_data._installed
                for action in (burn, ignite, residue, run, launch):
                    action.assert_not_called()
            print("clean import, lifespan, homepage, Scandoc, admission: passed")
        """), entrypoint],
        cwd=runtime, env=environment, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
