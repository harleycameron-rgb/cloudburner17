import importlib
import json
from pathlib import Path
import tomllib

from backend.scandoc_page import ASSETS, app


ROOT = Path(__file__).resolve().parents[2]


def test_root_configuration_imports_only_standalone_entrypoint():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    entrypoint = config["tool"]["vercel"]["entrypoint"]
    assert entrypoint == "backend.scandoc_page:app"
    module, attribute = entrypoint.split(":")
    assert getattr(importlib.import_module(module), attribute) is app
    assert (ROOT / "requirements.txt").read_text().strip() == "-r backend/requirements.txt"


def test_root_bundle_includes_all_preloaded_assets():
    config = json.loads((ROOT / "vercel.json").read_text())
    assert set(config["functions"]) == {"backend/scandoc_page.py"}
    pattern = config["functions"]["backend/scandoc_page.py"]["includeFiles"]
    bundled = {path.name for path in ROOT.glob(pattern + "/*") if path.is_file()}
    assert set(ASSETS) == {"index.html", "app.js", "model.js", "style.css"}
    assert set(ASSETS) <= bundled
