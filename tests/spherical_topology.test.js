import test from "node:test";
import assert from "node:assert/strict";
import {
  SHARED_ORIGIN, SphericalBurnHarness, sphericalGeometry,
<<<<<<< HEAD
  radialPlacement, verifySphericalEnvelope, runSphericalBurnHarness,
} from "../CLOUDBURNER17.js";
import { snapshot as nativeSnapshot } from "../src/burn_logic.js";
=======
  radialPlacement, verifySphericalEnvelope,
} from "../src/spherical_topology.js";
import { runSphericalBurnHarness } from "../CLOUDBURNER17.js";
>>>>>>> origin/main

function finish(h, id) {
  h.converge(id, [{ name: "caller-check", ok: true }]);
  h.retire(id);
  return h.burn(id);
}

test("shared origin and tilted basis form an orthonormal sphere frame", () => {
  const g = sphericalGeometry();
  assert.deepEqual(g.origin, SHARED_ORIGIN);
  assert.ok(Math.abs(g.shiftedAxis[2] - Math.cos(Math.PI/6)) < 1e-12);
  for (const a of g.basis) {
    assert.ok(Math.abs(Math.hypot(...a)-1) < 1e-12);
    for (const b of g.basis) if (a !== b)
      assert.ok(Math.abs(a.reduce((s, v, i) => s+v*b[i], 0)) < 1e-12);
  }
});

<<<<<<< HEAD
test("placement is deterministic across sessions with isolated native commitments", () => {
  const a = new SphericalBurnHarness(), b = new SphericalBurnHarness();
  const input = { id: "scene-11", content: "shared origin", layer: 511 };
  const one = a.admit(input), two = b.admit(input);
=======
test("placement is deterministic with the same geometry/content across sessions", () => {
  const a = new SphericalBurnHarness(), b = new SphericalBurnHarness();
  const one = a.admit({ id: "scene-11", content: "shared origin", layer: 511 });
  const two = b.admit({ id: "scene-11", content: "shared origin", layer: 511 });
>>>>>>> origin/main
  assert.deepEqual(one.placement, two.placement);
  assert.equal(one.topologyHash, two.topologyHash);
  assert.notEqual(one.commitment, two.commitment);
  const offset = one.placement.position.map((v, i) => v-SHARED_ORIGIN[i]);
  assert.ok(Math.abs(Math.hypot(...offset)-512) < 1e-10);
<<<<<<< HEAD
  finish(a, input.id);
  assert.equal(b.snapshot().modules[0].state, "admitted");
  finish(b, input.id);
  const native = nativeSnapshot().commitments;
  for (const module of [one, two]) {
    const record = native.find(r => r.moduleId === module.commitment);
    assert.equal(record.state, "burned");
    assert.equal(record.executionRevoked, true);
    assert.equal(record.ancestry[0].vector[0].invariant, true);
  }
=======
>>>>>>> origin/main
});

test("layer limits and invalid geometry fail before admission", () => {
  const h = new SphericalBurnHarness();
  for (const layer of [-1, 512, 0.5, "radial"])
    assert.throws(() => h.admit({ id: "bad", content: "x", layer }));
<<<<<<< HEAD
  for (const options of [
    { axis: [0, 0, 0] }, { origin: [Infinity, 0, 0] },
    { radius: -1 }, { radius: 1e6+1 }, { layerSpacing: 0 }, { tilt: NaN },
    { origin: Array(3) },
  ]) assert.throws(() => sphericalGeometry(options));
=======
  assert.throws(() => sphericalGeometry({ axis: [0, 0, 0] }));
  assert.throws(() => sphericalGeometry({ origin: [Infinity, 0, 0] }));
  assert.throws(() => sphericalGeometry({ radius: -1 }));
>>>>>>> origin/main
  assert.throws(() => radialPlacement(sphericalGeometry(), "invalid", 0));
  assert.equal(h.snapshot().modules.length, 0);
});

test("burn requires passing convergence then retirement", () => {
  const h = new SphericalBurnHarness();
  h.admit({ id: "a", content: "a" });
  assert.throws(() => h.burn("a"));
  assert.throws(() => h.retire("a"));
  assert.throws(() => h.converge("a", []));
<<<<<<< HEAD
  assert.throws(() => h.converge("a", Array(1)));
  assert.throws(() => h.converge("a", [{ name: "x", ok: "true" }]));
=======
>>>>>>> origin/main
  h.converge("a", [{ name: "failed", ok: false }]);
  assert.throws(() => h.retire("a"));
  finish(h, "a");
  assert.equal(h.snapshot().modules[0].state, "burned");
<<<<<<< HEAD
  assert.throws(() => h.converge("a", [{ name: "x", ok: true }]));
  assert.throws(() => h.retire("a"));
=======
>>>>>>> origin/main
});

test("dependencies must exist and burn before dependent retirement", () => {
  const h = new SphericalBurnHarness();
  assert.throws(() => h.admit({ id: "b", content: "b", dependencies: ["a"] }));
  h.admit({ id: "a", content: "a" });
<<<<<<< HEAD
  assert.throws(() => h.admit({ id: "b", content: "b", dependencies: Array(1) }));
  assert.throws(() => h.admit({ id: "b", content: "b", dependencies: ["a", "a"] }));
  h.admit({ id: "b", content: "b", dependencies: ["a"] });
  h.converge("b", [{ name: "pass", ok: true }]);
  assert.throws(() => h.retire("b"));
  h.converge("a", [{ name: "pass", ok: true }]); h.retire("a");
  assert.throws(() => h.retire("b"));
  h.burn("a"); h.retire("b"); h.burn("b");
  const s = h.snapshot(), expectedHead = s.head;
  assert.equal(verifySphericalEnvelope(s, expectedHead), true);
=======
  h.admit({ id: "b", content: "b", dependencies: ["a"] });
  h.converge("b", [{ name: "pass", ok: true }]);
  assert.throws(() => h.retire("b"));
  finish(h, "a");
  h.retire("b"); h.burn("b");
  const s = h.snapshot();
  assert.equal(verifySphericalEnvelope(s, s.head), true);
>>>>>>> origin/main
  assert.deepEqual(s.events[1].dependencies, ["a"]);
});

test("identical retries are deduplicated and changed content is rejected", () => {
  const h = new SphericalBurnHarness();
  const input = { id: "a", content: "a", layer: 3 };
  const first = h.admit(input);
  assert.deepEqual(h.admit(input), first);
  assert.throws(() => h.admit({ ...input, content: "changed" }));
<<<<<<< HEAD
  assert.throws(() => h.admit({ ...input, layer: 4 }));
  const burn = finish(h, "a");
  assert.deepEqual(h.burn("a"), burn);
  assert.equal(h.admit(input).state, "burned");
=======
  const burn = finish(h, "a");
  assert.deepEqual(h.burn("a"), burn);
>>>>>>> origin/main
  assert.equal(h.snapshot().events.length, 1);
});

test("two burns form both lifecycle and spherical-envelope continuity", () => {
  const h = new SphericalBurnHarness();
<<<<<<< HEAD
  for (const id of ["a", "b"]) { h.admit({ id, content: id }); finish(h, id); }
  const s = h.snapshot(), expectedHead = s.head;
  assert.equal(s.events[1].previousEnvelope, s.events[0].envelopeHash);
  assert.equal(s.events[1].lifecycle.previousEvent, s.events[0].lifecycleHash);
  assert.equal(verifySphericalEnvelope(JSON.parse(JSON.stringify(s)), expectedHead), true);
  assert.equal(verifySphericalEnvelope(s), false);
});

test("geometry/event tampering, truncation and reordering fail against retained head", () => {
  const h = new SphericalBurnHarness();
  for (const id of ["a", "b"]) { h.admit({ id, content: id }); finish(h, id); }
  const original = h.snapshot(), expectedHead = original.head;
  for (const mutate of [
    s => { s.sphere.origin[0]++; },
    s => { s.sphere.basis[0][0]++; },
    s => { s.events[0].placement.position[0]++; },
    s => { s.events[0].lifecycle.timestamp++; },
    s => { s.events.pop(); s.head = s.events[0].envelopeHash; s.lifecycleHead = s.events[0].lifecycleHash; },
=======
  for (const id of ["a", "b"]) {
    h.admit({ id, content: id }); finish(h, id);
  }
  const s = h.snapshot();
  assert.equal(s.events[1].previousEnvelope, s.events[0].envelopeHash);
  assert.equal(s.events[1].lifecycle.previousEvent, s.events[0].lifecycleHash);
  assert.equal(verifySphericalEnvelope(JSON.parse(JSON.stringify(s)), s.head), true);
  assert.equal(verifySphericalEnvelope(s), false);
});

test("geometry/event tampering, truncation and reordering fail against trusted head", () => {
  const h = new SphericalBurnHarness();
  for (const id of ["a", "b"]) {
    h.admit({ id, content: id }); finish(h, id);
  }
  const original = h.snapshot();
  for (const mutate of [
    s => { s.sphere.origin[0]++; },
    s => { s.events[0].placement.position[0]++; },
    s => { s.events[0].lifecycle.timestamp++; },
    s => { s.events.pop(); },
>>>>>>> origin/main
    s => { s.events.reverse(); },
    s => { s.events[1].dependencies = ["unknown"]; },
    s => { s.signature = "pretend signature"; },
    s => { s.bitcoinAnchor = { confirmed: true }; },
  ]) {
    const s = structuredClone(original); mutate(s);
<<<<<<< HEAD
    assert.equal(verifySphericalEnvelope(s, expectedHead), false);
=======
    assert.equal(verifySphericalEnvelope(s, original.head), false);
>>>>>>> origin/main
  }
});

test("different origin changes topology and trusted envelope identity", () => {
  const a = new SphericalBurnHarness();
  const b = new SphericalBurnHarness({ origin: [0, 0, 0] });
<<<<<<< HEAD
  a.admit({ id: "a", content: "a" }); b.admit({ id: "a", content: "a" });
=======
  a.admit({ id: "a", content: "a" });
  b.admit({ id: "a", content: "a" });
>>>>>>> origin/main
  finish(a, "a"); finish(b, "a");
  assert.notEqual(a.snapshot().genesis, b.snapshot().genesis);
  assert.equal(verifySphericalEnvelope(b.snapshot(), a.snapshot().head), false);
});

test("caller mutations cannot edit internal geometry, module state or pulses", () => {
<<<<<<< HEAD
  const origin = [1024, 1024, 0], h = new SphericalBurnHarness({ origin });
  origin[0] = 0;
  const admitted = h.admit({ id: "a", content: "a" });
  admitted.state = "burned"; admitted.placement.position[0] = 0;
  assert.equal(h.snapshot().modules[0].state, "admitted");
  const burn = finish(h, "a"); burn.lifecycle.layer = 999;
  const s = h.snapshot(); s.sphere.origin[0] = 0; s.events.length = 0;
=======
  const origin = [1024, 1024, 0];
  const h = new SphericalBurnHarness({ origin });
  origin[0] = 0;
  const admitted = h.admit({ id: "a", content: "a" });
  admitted.state = "burned";
  admitted.placement.position[0] = 0;
  assert.equal(h.snapshot().modules[0].state, "admitted");
  const burn = finish(h, "a");
  burn.lifecycle.layer = 999;
  const s = h.snapshot();
  s.sphere.origin[0] = 0; s.events.length = 0;
>>>>>>> origin/main
  const actual = h.snapshot();
  assert.equal(actual.sphere.origin[0], 1024);
  assert.equal(actual.events.length, 1);
  assert.equal(verifySphericalEnvelope(actual, actual.head), true);
});

test("raw content, signing claims and external timestamps are not exported", () => {
  const h = new SphericalBurnHarness();
  h.admit({ id: "a", content: "secret-raw-sample" }); finish(h, "a");
  const s = h.snapshot();
  assert.equal(JSON.stringify(s).includes("secret-raw-sample"), false);
<<<<<<< HEAD
  assert.equal(s.signature, null); assert.equal(s.bitcoinAnchor, null);
=======
  assert.equal(s.signature, null);
  assert.equal(s.bitcoinAnchor, null);
>>>>>>> origin/main
  assert.equal("timestampProof" in s.events[0].lifecycle, false);
});

test("empty envelope verifies only against its supplied genesis head", () => {
<<<<<<< HEAD
  const s = new SphericalBurnHarness().snapshot();
=======
  const h = new SphericalBurnHarness(), s = h.snapshot();
>>>>>>> origin/main
  assert.equal(verifySphericalEnvelope(s, s.head), true);
  assert.equal(verifySphericalEnvelope(s, "0".repeat(128)), false);
});

test("public entrypoint runs the real lifecycle with a custom tilted sphere", () => {
  const s = runSphericalBurnHarness([
    { id: "root", content: "origin", layer: 0 },
    { id: "child", content: "shell", layer: 511, dependencies: ["root"] },
  ], { axis: [1, 2, 3], tilt: -Math.PI/4 });
  assert.equal(s.events.length, 2);
  assert.equal(verifySphericalEnvelope(s, s.head), true);
});

<<<<<<< HEAD
test("convenience harness stops on failure and deduplicates scene retries", () => {
=======
test("convenience harness stops on a failed caller check", () => {
>>>>>>> origin/main
  assert.throws(() => runSphericalBurnHarness([
    { id: "bad", content: "x", checks: [{ name: "failed", ok: false }] },
  ]), /passing convergence/);
  assert.throws(() => runSphericalBurnHarness([]));
<<<<<<< HEAD
  const scene = { id: "a", content: "x" };
  assert.equal(runSphericalBurnHarness([scene, scene]).events.length, 1);
  assert.throws(() => runSphericalBurnHarness([scene, { ...scene, content: "y" }]),
    /Changed-content retry/);
=======
>>>>>>> origin/main
});
