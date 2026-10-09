import test from "node:test";
import assert from "node:assert/strict";
import { runSphericalBurnHarness } from "../burn-harness-spherical.js";
import {
  SphereShiftGate, verifySphereShifts, gateSymbolSVG,
} from "../src/sphere_shift_gate.js";

function source() {
  return runSphericalBurnHarness([
    { id: "origin", content: "a", layer: 0 },
    { id: "surface", content: "b", layer: 511, dependencies: ["origin"] },
  ]);
}

test("shift emits exactly two linked firings and changes the gate glyph state", () => {
  const s = source(), g = new SphereShiftGate(s, s.head);
  assert.equal(g.snapshot().gateSymbol, "sphere-ready");
  const e = g.shift("segment-a", Math.PI/6), h = g.snapshot();
  assert.equal(e.pair.length, 2);
  assert.equal(e.pair[0].kind, "surface-projection");
  assert.equal(e.pair[1].kind, "linear-checkpoint");
  assert.equal(e.pair[0].segmentHash, e.pair[1].segmentHash);
  assert.equal(h.gateSymbol, "dual-fired-unanchored");
  assert.equal(verifySphereShifts(h, s.head, h.head), true);
});

test("twist preserves origin, radial length, source commitments and ordered source", () => {
  const s = source(), before = structuredClone(s);
  const g = new SphereShiftGate(s, s.head);
  const e = g.shift("a", Math.PI/6);
  assert.deepEqual(e.segment.fromGeometry.origin, e.segment.toGeometry.origin);
  for (const [i, p] of e.surface.entries()) {
    const delta = p.placement.position.map((v, j) => v-s.sphere.origin[j]);
    assert.ok(Math.abs(Math.hypot(...delta)-s.events[i].placement.radius) < 1e-10);
    assert.equal(p.topologyHash, s.events[i].topologyHash);
    assert.equal(p.sourceEnvelope, s.events[i].envelopeHash);
  }
  assert.deepEqual(s, before);
});

test("invalid or missing half firing and modified projection fail verification", () => {
  const s = source(), g = new SphereShiftGate(s, s.head);
  g.shift("a", .2);
  const h = g.snapshot();
  for (const change of [
    x => x.events[0].pair.pop(),
    x => { x.events[0].pair[1].segmentHash = "0".repeat(128); },
    x => { x.events[0].surface[0].placement.position[0]++; },
    x => { x.events[0].pair[1].bitcoinAnchor = { confirmed: true }; },
  ]) {
    const modified = structuredClone(h); change(modified);
    assert.equal(verifySphereShifts(modified, s.head, h.head), false);
  }
});

test("ordered shift history detects truncation, reordering and wrong trusted heads", () => {
  const s = source(), g = new SphereShiftGate(s, s.head);
  g.shift("a", .2); g.shift("b", -.1);
  const h = g.snapshot();
  assert.equal(verifySphereShifts(h, s.head, h.head), true);
  const truncated = structuredClone(h); truncated.events.pop();
  assert.equal(verifySphereShifts(truncated, s.head, h.head), false);
  const reversed = structuredClone(h); reversed.events.reverse();
  assert.equal(verifySphereShifts(reversed, s.head, h.head), false);
  assert.equal(verifySphereShifts(h, "0".repeat(128), h.head), false);
  assert.equal(verifySphereShifts(h, s.head, "0".repeat(128)), false);
});

test("failed shifts commit nothing and retries do not fire twice", () => {
  const s = source(), g = new SphereShiftGate(s, s.head);
  const initial = g.snapshot();
  for (const twist of [NaN, Infinity]) {
    assert.throws(() => g.shift("a", twist));
  }
  assert.throws(() => g.shift("", .1));
  assert.deepEqual(g.snapshot(), initial);
  const e = g.shift("a", .1);
  assert.deepEqual(g.shift("a", .1), e);
  assert.throws(() => g.shift("a", .2));
  assert.equal(g.snapshot().events.length, 1);
});

test("snapshots and returned pairs are isolated from caller mutation", () => {
  const s = source(), g = new SphereShiftGate(s, s.head);
  const e = g.shift("a", .1);
  e.pair.length = 0; s.events.length = 0;
  const h = g.snapshot(); h.events.length = 0;
  assert.equal(g.snapshot().events.length, 1);
  assert.equal(g.snapshot().events[0].pair.length, 2);
});

test("atomic gas is separate conceptual geometry and date remains unsubmitted", () => {
  const s = source(), g = new SphereShiftGate(s, s.head);
  const e = g.shift("a", .1);
  assert.equal(e.atomicGas.evidence, "unverified");
  assert.equal(e.atomicGas.geometry, "separate-conceptual-origin");
  assert.equal(e.atomicity, "single-synchronous-memory-commit");
  assert.equal(e.pair[1].timestampState, "not-submitted");
  assert.equal(e.pair[1].bitcoinAnchor, null);
  assert.equal(g.snapshot().signature, null);
});

test("glyphs visibly differ and cannot claim confirmed Bitcoin anchoring", () => {
  assert.notEqual(
    gateSymbolSVG("sphere-ready"),
    gateSymbolSVG("dual-fired-unanchored"),
  );
  assert.match(gateSymbolSVG("dual-fired-unanchored"), /UNANCHORED/);
  assert.throws(() => gateSymbolSVG("bitcoin-confirmed"));
});
