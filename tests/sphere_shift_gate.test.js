import test from "node:test";
import assert from "node:assert/strict";
<<<<<<< HEAD
import {
  runSphericalBurnHarness, SphericalBurnHarness,
  SphereShiftGate, verifySphereShifts, gateSymbolSVG,
} from "../CLOUDBURNER17.js";
=======
import { runSphericalBurnHarness } from "../burn-harness-spherical.js";
import {
  SphereShiftGate, verifySphereShifts, gateSymbolSVG,
} from "../src/sphere_shift_gate.js";
>>>>>>> origin/main

function source() {
  return runSphericalBurnHarness([
    { id: "origin", content: "a", layer: 0 },
    { id: "surface", content: "b", layer: 511, dependencies: ["origin"] },
  ]);
}

test("shift emits exactly two linked firings and changes the gate glyph state", () => {
  const s = source(), g = new SphereShiftGate(s, s.head);
  assert.equal(g.snapshot().gateSymbol, "sphere-ready");
<<<<<<< HEAD
  const initial = g.snapshot();
  assert.equal(verifySphereShifts(initial, s.head, initial.head), true);
=======
>>>>>>> origin/main
  const e = g.shift("segment-a", Math.PI/6), h = g.snapshot();
  assert.equal(e.pair.length, 2);
  assert.equal(e.pair[0].kind, "surface-projection");
  assert.equal(e.pair[1].kind, "linear-checkpoint");
  assert.equal(e.pair[0].segmentHash, e.pair[1].segmentHash);
  assert.equal(h.gateSymbol, "dual-fired-unanchored");
  assert.equal(verifySphereShifts(h, s.head, h.head), true);
});

test("twist preserves origin, radial length, source commitments and ordered source", () => {
<<<<<<< HEAD
  const s = source(), before = structuredClone(s), g = new SphereShiftGate(s, s.head);
  const e = g.shift("a", Math.PI/6);
  assert.deepEqual(e.segment.fromGeometry.origin, e.segment.toGeometry.origin);
  assert.notDeepEqual(e.segment.fromGeometry.basis, e.segment.toGeometry.basis);
=======
  const s = source(), before = structuredClone(s);
  const g = new SphereShiftGate(s, s.head);
  const e = g.shift("a", Math.PI/6);
  assert.deepEqual(e.segment.fromGeometry.origin, e.segment.toGeometry.origin);
>>>>>>> origin/main
  for (const [i, p] of e.surface.entries()) {
    const delta = p.placement.position.map((v, j) => v-s.sphere.origin[j]);
    assert.ok(Math.abs(Math.hypot(...delta)-s.events[i].placement.radius) < 1e-10);
    assert.equal(p.topologyHash, s.events[i].topologyHash);
    assert.equal(p.sourceEnvelope, s.events[i].envelopeHash);
<<<<<<< HEAD
    assert.notDeepEqual(p.placement.position, s.events[i].placement.position);
  }
  assert.deepEqual(s, before);
  assert.deepEqual(g.snapshot().source, before);
});

test("invalid or missing half firing and modified projection fail verification", () => {
  const s = source(), g = new SphereShiftGate(s, s.head); g.shift("a", .2);
  const h = g.snapshot(), expectedHead = h.head;
  for (const change of [
    x => x.events[0].pair.pop(),
    x => x.events[0].pair.reverse(),
    x => { x.events[0].pair[1].segmentHash = "0".repeat(128); },
    x => { x.events[0].surface[0].placement.position[0]++; },
    x => { x.events[0].pair[1].bitcoinAnchor = { confirmed: true }; },
    x => { x.events[0].pair[1].timestampState = "submitted"; },
    x => { x.signature = "pretend"; },
    x => { x.bitcoinAnchor = {}; },
  ]) {
    const modified = structuredClone(h); change(modified);
    assert.equal(verifySphereShifts(modified, s.head, expectedHead), false);
  }
});

test("ordered shift history detects truncation, reordering and wrong retained heads", () => {
  const s = source(), g = new SphereShiftGate(s, s.head); g.shift("a", .2); g.shift("b", -.1);
  const h = g.snapshot(), expectedHead = h.head;
  assert.equal(verifySphereShifts(h, s.head, expectedHead), true);
  const truncated = structuredClone(h); truncated.events.pop();
  truncated.head = truncated.events[0].eventHash;
  truncated.geometry = truncated.events[0].segment.toGeometry;
  assert.equal(verifySphereShifts(truncated, s.head, expectedHead), false);
  const reversed = structuredClone(h); reversed.events.reverse();
  assert.equal(verifySphereShifts(reversed, s.head, expectedHead), false);
  assert.equal(verifySphereShifts(h, "0".repeat(128), expectedHead), false);
  assert.equal(verifySphereShifts(h, s.head, "0".repeat(128)), false);
  assert.equal(verifySphereShifts(h, s.head), false);
});

test("failed shifts commit nothing and retries do not fire twice", () => {
  const s = source(), g = new SphereShiftGate(s, s.head), initial = g.snapshot();
  for (const twist of [NaN, Infinity]) assert.throws(() => g.shift("a", twist));
  assert.throws(() => g.shift("", .1)); assert.deepEqual(g.snapshot(), initial);
  const e = g.shift("a", .1); assert.deepEqual(g.shift("a", .1), e);
  assert.throws(() => g.shift("a", .2)); assert.equal(g.snapshot().events.length, 1);
  assert.throws(() => new SphereShiftGate(s));
  assert.throws(() => new SphereShiftGate(s, "0".repeat(128)));
  const empty = new SphericalBurnHarness().snapshot();
  const emptyGate = new SphereShiftGate(empty, empty.head), before = emptyGate.snapshot();
  assert.throws(() => emptyGate.shift("empty", .1), /No burned trajectory/);
  assert.deepEqual(emptyGate.snapshot(), before);
  g.shift("huge", Number.MAX_VALUE);
  const prior = g.snapshot();
  assert.throws(() => g.shift("overflow", Number.MAX_VALUE));
  assert.deepEqual(g.snapshot(), prior);
});

test("snapshots and returned pairs are isolated from caller mutation", () => {
  const s = source(), g = new SphereShiftGate(s, s.head), e = g.shift("a", .1);
=======
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
>>>>>>> origin/main
  e.pair.length = 0; s.events.length = 0;
  const h = g.snapshot(); h.events.length = 0;
  assert.equal(g.snapshot().events.length, 1);
  assert.equal(g.snapshot().events[0].pair.length, 2);
});

test("atomic gas is separate conceptual geometry and date remains unsubmitted", () => {
<<<<<<< HEAD
  const s = source(), g = new SphereShiftGate(s, s.head), e = g.shift("a", .1);
=======
  const s = source(), g = new SphereShiftGate(s, s.head);
  const e = g.shift("a", .1);
>>>>>>> origin/main
  assert.equal(e.atomicGas.evidence, "unverified");
  assert.equal(e.atomicGas.geometry, "separate-conceptual-origin");
  assert.equal(e.atomicity, "single-synchronous-memory-commit");
  assert.equal(e.pair[1].timestampState, "not-submitted");
  assert.equal(e.pair[1].bitcoinAnchor, null);
  assert.equal(g.snapshot().signature, null);
<<<<<<< HEAD
  assert.equal(g.snapshot().bitcoinAnchor, null);
});

test("glyphs visibly differ and cannot claim confirmed Bitcoin anchoring", () => {
  assert.notEqual(gateSymbolSVG("sphere-ready"), gateSymbolSVG("dual-fired-unanchored"));
=======
});

test("glyphs visibly differ and cannot claim confirmed Bitcoin anchoring", () => {
  assert.notEqual(
    gateSymbolSVG("sphere-ready"),
    gateSymbolSVG("dual-fired-unanchored"),
  );
>>>>>>> origin/main
  assert.match(gateSymbolSVG("dual-fired-unanchored"), /UNANCHORED/);
  assert.throws(() => gateSymbolSVG("bitcoin-confirmed"));
});
