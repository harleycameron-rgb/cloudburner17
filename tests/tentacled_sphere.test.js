import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import test from "node:test";
import { createTentacledSphere } from "../src/tentacled_sphere.js";
import { verifySphericalEnvelope } from "../src/spherical_topology.js";

const commit = value => createHash("sha512")
  .update(JSON.stringify(value)).digest("hex");

test("eight arms attach to verified native burns with a common core", () => {
  const result = createTentacledSphere({ sphere: { origin: [3, -2, 1], radius: 2 } });
  assert.equal(result.arms.length, 8);
  assert.equal(result.source.events.length, 9);
  assert.equal(verifySphericalEnvelope(result.source, result.source.head), true);
  for (const [i, arm] of result.arms.entries()) {
    assert.deepEqual(arm.points[0], arm.attachment);
    assert.equal(arm.points.length, 33);
    assert.deepEqual(result.source.events[i+1].dependencies, ["sphere-core"]);
    assert.equal(arm.receipt, result.source.events[i+1].envelopeHash);
    assert.ok(arm.points.flat().every(Number.isFinite));
    assert.ok(Math.abs(Math.hypot(...arm.attachment.map((x,k) => x-result.source.sphere.origin[k]))-2)<1e-10);
  }
  assert.equal(result.source.signature, null);
  assert.equal(result.source.bitcoinAnchor, null);
  assert.equal(result.upstreamIntegration, false);
  assert.equal(result.authentication, "backend-required");
});

test("arm geometry repeats while session receipts stay isolated", () => {
  const a = createTentacledSphere();
  const b = createTentacledSphere();
  assert.deepEqual(a.arms.map(x=>x.points), b.arms.map(x=>x.points));
  assert.deepEqual(a.arms.map(x=>x.geometryCommitment), b.arms.map(x=>x.geometryCommitment));
  assert.notEqual(a.source.genesis, b.source.genesis);
  a.arms[0].points[0][0] = 999;
  assert.equal(verifySphericalEnvelope(b.source, b.source.head), true);
});

test("invalid or unbounded tentacle parameters fail", () => {
  for (const options of [{segments:1}, {segments:257}, {length:0},
    {length:Infinity}, {turns:NaN}, {turns:17}, {amplitude:-1}]) {
    assert.throws(()=>createTentacledSphere(options), TypeError);
  }
});

test("synthetic traces link sources, transforms and geometry without claiming app integration", () => {
  const result = createTentacledSphere({
    sphere: { origin: [-3, 2, 5], axis: [1, 2, 3], tilt: 0.4, radius: 3 },
    segments: 8, length: 4, turns: -2, amplitude: 0.5,
  });
  for (const [i, arm] of result.arms.entries()) {
    assert.equal(arm.id, `arm-${i + 1}`);
    assert.equal(arm.status, "synthetic-tested");
    assert.deepEqual(arm.mapping, {
      status: "pending", repository: null, htmlPath: null,
      orrery: { fields: null, units: null, timeReference: null },
      orrerySourceCommitment: null,
    });
    const { trace } = arm;
    assert.equal(trace.source.kind, "synthetic-declared-scene");
    assert.equal(trace.source.scene.id, arm.id);
    assert.equal(trace.source.topologyHash, result.source.events[i + 1].topologyHash);
    assert.deepEqual(trace.frame.sphere, result.source.sphere);
    assert.equal(trace.frame.timeReference, null);
    assert.equal(arm.sourceCommitment, commit(trace.source));
    const body = {
      schema: "tentacled-sphere-geometry/1",
      id: arm.id, mapping: arm.mapping, trace,
      sourceCommitment: arm.sourceCommitment,
      attachment: arm.attachment, points: arm.points,
    };
    assert.equal(arm.geometryCommitment, commit(body));
    const { segments, length, turns, amplitude, direction, tangentU, tangentV } =
      trace.transformation;
    const reconstructed = Array.from({ length: segments + 1 }, (_, j) => {
      const t = j / segments;
      return trace.frame.sphere.origin.map((o, k) => o + trace.frame.sphere.radius *
        ((1 + length*t)*direction[k] + amplitude*t *
          (Math.cos(2*Math.PI*turns*t)*tangentU[k] +
           Math.sin(2*Math.PI*turns*t)*tangentV[k])));
    });
    assert.deepEqual(arm.points, reconstructed);
    arm.points[1][0] += 1;
    assert.notEqual(arm.geometryCommitment, commit(body));
    arm.points[1][0] -= 1;
    trace.transformation.turns += 1;
    assert.notEqual(arm.geometryCommitment, commit(body));
  }
  result.arms[0].trace.frame.sphere.origin[0] = 999;
  assert.deepEqual(result.arms[1].trace.frame.sphere.origin, [-3, 2, 5]);
  assert.equal(verifySphericalEnvelope(result.source, result.source.head), true);
});
