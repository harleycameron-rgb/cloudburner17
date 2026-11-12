"""Static regression for the browser-local viewport/chaos-lab preview.

Checks wiring and hardcoded safety boundaries, NOT browser/runtime security.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "backend/scandoc/index.html"
JS = ROOT / "backend/scandoc/app.js"
CSS = ROOT / "backend/scandoc/style.css"


def test_viewport_is_not_firing_surface():
    html = HTML.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    assert 'id="lab-source"' in html
    assert 'id="lab-sandbox"' in html
    assert 'id="lab-splat"' in html
    assert 'NATIVE GATE CLOSED' in html
    assert "#lab-source{pointer-events:none" in css


def test_sandbox_inputs_are_observer_side_only():
    js = JS.read_text(encoding="utf-8")
    assert 'baseline = Object.freeze(' in js
    assert 'const residuals=observation.map' in js
    assert 'candidate_mismatches' in js
    assert 'confirmed_false_invariants:0' in js
    assert 'native_gate:"CLOSED"' in js
    assert 'source_modified:false' in js
    assert 'addEventListener("click"' in js
    assert "No source mutation" not in js  # no misleading elevated proof claim


def test_source_and_sandbox_have_separate_canvases():
    html = HTML.read_text(encoding="utf-8")
    assert html.count('id="lab-source"') == 1
    assert html.count('id="lab-sandbox"') == 1
    assert 'Double splat (sandbox only)' in html


def test_missing_canvas_context_disables_lab_controls():
    js = JS.read_text(encoding="utf-8")
    assert "if (!ctxA || !ctxB)" in js
    assert 'document.querySelectorAll(".lab input, .lab button")' in js
    assert "control.disabled = true" in js
    assert "Chaos Lab unavailable" in js
