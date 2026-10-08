import assert from "node:assert/strict";
import test from "node:test";
import {
  hashPrinter,
  instrumentPanelSnapshot,
  pulseGauge,
  recordSession,
  safetyLight,
  tapSurface,
  triggerBridge,
  vectorInspector,
  wobbleMeter,
} from "../CLOUDBURNER17.js";

test("instrument panel records taps, a session, and bridge safety", () => {
  const firstTap = tapSurface("panel-alpha");
  const secondTap = tapSurface("panel-beta");

  assert.equal(firstTap.name, "panel-alpha");
  assert.equal(firstTap.ok, true);
  assert.equal(firstTap.wobble, 0);
  assert.match(firstTap.hash, /^[0-9a-f]{8}$/);
  assert.notEqual(firstTap.hash, secondTap.hash);
  assert.equal(hashPrinter(), secondTap.hash);

  const session = recordSession();
  assert.equal(session.invariantPulse, true);
  assert.equal(pulseGauge(), true);
  assert.equal(wobbleMeter(), 0);
  assert.equal(vectorInspector().length, 2);

  const bridge = triggerBridge();
  assert.equal(bridge.invariantPulse, true);
  assert.equal(safetyLight(), "SAFE");

  const snapshot = instrumentPanelSnapshot();
  assert.deepEqual(snapshot.events, ["panel-alpha", "panel-beta"]);
  assert.equal(snapshot.status, "INVARIANT_TAP_PANEL_ACTIVE");
  assert.equal(snapshot.safety, "SAFE");
});
