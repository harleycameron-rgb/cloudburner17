from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_canary_viewport_is_isolated():
    src=(ROOT/'backend/scandoc/root_canary_viewport.js').read_text()
    html=(ROOT/'backend/scandoc/index.html').read_text()
    app=(ROOT/'backend/scandoc/app.js').read_text()
    assert "from '../../root_disruptor.mjs'" in src
    assert 'mountRootCanary();' in app
    assert 'root-canary-canvas' in html
    assert 'root-canary-inject' in html
    assert 'root-canary-clear' in html
    assert 'SYNTHETIC FIXTURE ONLY' in html
    assert "diagnose(base,current)" in src
    assert "current=disrupt(current)" in src
    assert "current=move(base," in src
    assert "fetch(" not in src
    assert "localStorage" not in src
    assert "sessionStorage" not in src
    assert "nativeGate='OPEN'" not in src
