import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { MODEL, CHANNELS, canonical, digest, baseline, medianCore, syntheticDemo,
  validateTrajectory, verifyBoundary, adaptSourceChannels, contextSeed, createController, toCSV,
} from "../backend/scandoc/model.js";

const clone = value => structuredClone(value);
test("canonical model, complete Cube, faces and trajectory hashes are deterministic", async () => {
  const a = await syntheticDemo(), b = await syntheticDemo();
  assert.deepEqual(a, b);
  assert.equal(await digest({ b: 2, a: 1 }), await digest({ a: 1, b: 2 }));
  assert.equal(a.cubeDigest, await digest(a.cubeState));
  assert.equal(a.cubeState.geometry.vertices.length, 8);
  assert.equal(a.cubeState.geometry.faceVertices.length, 6);
  assert.equal(a.trajectoryDigest, await digest(a.trajectory));
  assert.equal(new Set(a.perFaceDigests).size, 6);
  const changed = clone(MODEL);
  changed.frequency.value = 0.5;
  const c = await syntheticDemo(changed);
  assert.notEqual(c.modelDigest, a.modelDigest);
  assert.notEqual(c.cubeDigest, a.cubeDigest);
  assert.equal(c.trajectoryDigest, a.trajectoryDigest);
  assert.notDeepEqual(c.perFaceDigests, a.perFaceDigests);
  assert.throws(() => { a.trajectory[0].sphere.center[0] = 0; }, TypeError);
  for (const value of [NaN, Infinity, undefined, () => 0]) assert.throws(() => canonical(value));
  assert.throws(() => canonical(new Array(2)));
});
test("proper Q, positive scale, baseline formula and even six-leg median", async () => {
  assert.deepEqual(baseline(MODEL.baseline)[0], [1025, 1024, 0]);
  assert.deepEqual(baseline({ C: [1, 2, 3], ell0: 2, Q: [[0, -1, 0], [1, 0, 0], [0, 0, 1]] })[0], [1, 4, 3]);
  for (const patch of [{ ell0: 0 }, { ell0: -1 }, { ell0: NaN },
    { Q: [[-1, 0, 0], [0, 1, 0], [0, 0, 1]] },
    { Q: [[1, 1, 0], [0, 1, 0], [0, 0, 1]] }]) {
    assert.throws(() => baseline({ ...clone(MODEL.baseline), ...patch }));
  }
  const state = clone((await syntheticDemo()).trajectory[0]);
  const lengths = [5, 0, 3, 1, 4, 2];
  state.faces.forEach((f, i) => { f.position[0] += lengths[i]; });
  assert.equal(medianCore(state, MODEL.baseline), 2.5);
});
test("velocity, radius, frame, fixed anchors, six faces and increasing time", async () => {
  const demo = await syntheticDemo(), last = demo.trajectory.at(-1);
  assert.equal(last.sphere.radius, 0.8);
  assert.deepEqual(last.sphere.center, [1025.6, 1024, 0]);
  assert.deepEqual(last.sphere.velocity, [-0.1, 0, 0]);
  assert.ok(Math.abs(demo.sentinelSeparation - 1.6) < 1e-9);
  assert.ok(Math.abs(demo.median - 0.2) < 1e-9);
  const corruptions = [
    s => s[1].faces.pop(), s => { s[1].faces[0].anchor[0] += 1; },
    s => { s[1].sphere.center[0] = Infinity; }, s => { s[1].sphere.radius = 0; },
    s => { s[1].tick = s[0].tick; }, s => { s[1].time = s[0].time; },
    s => { s[1].frame.units.length = "metres"; }, s => { s[1].sphere.velocity[0] = 1; },
  ];
  for (const corrupt of corruptions) {
    const states = clone(demo.trajectory); corrupt(states);
    assert.throws(() => validateTrajectory(states));
  }
  for (const patch of [{ ticks: 1 }, { ticks: 257 }, { step: 0 }, { faceContractionRate: 1 },
    { initialRadius: -1 }, { velocity: [NaN, 0, 0] }]) {
    const model = clone(MODEL); Object.assign(model.evolution, patch);
    await assert.rejects(syntheticDemo(model));
  }
  const model = clone(MODEL); model.frame.origin[0]++;
  await assert.rejects(syntheticDemo(model), /Shared origin/);
  for (const mutate of [
    m => { m.frequency.value = 0; }, m => { m.frequency.physical = true; },
    m => { m.frequency.value = 1e308; },
    m => { m.frequency.units = "Hz"; }, m => { m.provenance.measured = true; },
    m => { m.rendering.torsionRule = "unversioned"; }, m => { m.channels.pop(); },
  ]) {
    const changed = clone(MODEL); mutate(changed);
    await assert.rejects(syntheticDemo(changed));
  }
});
test("strict v0.6 unresolved evidence, containment, max-distance and actual endpoint", async () => {
  const demo = await syntheticDemo();
  assert.equal(demo.boundary.transitionAuthorized, false);
  assert.equal(demo.boundary.structuralMeltingAttachment, false);
  assert.ok(demo.boundary.unresolved.includes("actual endpoint missing"));
  const evidence = { kind: "measured", receipt: "untrusted-test-string", originHash: "untrusted-test-string",
    six: 1, seven: 1, residue: 0, inner: 1, outer: 2, endpoint: demo.trajectory.at(-1).sphere.center };
  const model = clone(MODEL); model.policies.closureDistance = 10;
  const result = verifyBoundary(demo.trajectory, evidence, model);
  assert.equal(result.status, "unresolved"); // even supplied claims confer no authority
  assert.equal(result.transitionAuthorized, false);
  for (const patch of [{ seven: 0 }, { six: 1e-12 }, { seven: NaN }])
    assert.ok(verifyBoundary(demo.trajectory, { ...evidence, ...patch }, model).unresolved.includes("six/seven denominator unresolved"));
  for (const patch of [{ residue: 2 }, { inner: 3 }, { residue: -1 }])
    assert.ok(verifyBoundary(demo.trajectory, { ...evidence, ...patch }, model).failed.includes("nested containment"));
  assert.ok(verifyBoundary(demo.trajectory, evidence).failed.includes("max-distance closure"));
  assert.ok(verifyBoundary(demo.trajectory, { ...evidence, endpoint: [0, 0, 0] }, model).failed.includes("actual endpoint proximity"));
  const stationary = clone(demo.trajectory);
  stationary.forEach(s => {
    s.faces = clone(stationary[0].faces); s.sphere.center = clone(stationary[0].sphere.center);
    s.sphere.velocity = [0, 0, 0];
  });
  assert.ok(verifyBoundary(stationary, evidence, model).failed.includes("positive inward mean-radius closure rate"));
  model.policies.segment = "linear";
  const endpoint = clone(demo.trajectory.at(-1).sphere.center); endpoint[0] += 0.05;
  const crossing = verifyBoundary(demo.trajectory, { ...evidence, endpoint }, model);
  assert.equal(crossing.segmentIntersection, true);
  assert.ok(crossing.failed.includes("actual endpoint proximity"));
});
test("handshake validates full seed and checkpoint; immutable observation and separate next-tick forecast", async () => {
  const demo = await syntheticDemo(), checkpoint = await contextSeed(demo);
  await assert.rejects(createController(demo, { ...checkpoint, seedHash: "bad" }));
  const controller = await createController(demo, checkpoint);
  const before = await digest(controller.observed);
  const next = clone(demo.trajectory.at(-1));
  next.tick++; next.time++;
  next.sphere.center[0] -= 0.1; next.sphere.radius -= 0.05;
  const body = clone(controller.body);
  const result = await controller.suppliedFiringResult({ body, proposals: [next] });
  assert.equal(result.stream, "forecast");
  assert.equal(controller.forecast().length, 1);
  assert.equal(await digest(controller.observed), before);
  assert.equal(controller.observed.length, demo.trajectory.length);
  assert.throws(() => { result.states[0].tick++; });
  await assert.rejects(controller.suppliedFiringResult({ body, proposals: [demo.trajectory[0]] }));
  for (const mutate of [
    b => { b.frequency.value = 9; }, b => { b.radiusPrefix[0].radius = 9; },
    b => { b.extra = "raw"; }, b => { delete b.sentinel; },
  ]) {
    const changed = clone(body); mutate(changed);
    await assert.rejects(controller.suppliedFiringResult({ body: changed, proposals: [next] }));
  }
  const tampered = clone(demo); tampered.trajectory[0].sphere.radius = 9;
  await assert.rejects(createController(tampered, checkpoint));
  assert.equal(controller.requestContext().originStatus, "unresolved");
  assert.equal(controller.requestContext().transmission, "disabled");
  for (const key of ["faces", "position", "anchor", "deltas", "rawTelemetry", "source"]) {
    assert.ok(!JSON.stringify(body).includes(`"${key}":`));
  }
});
test("synthetic labels, eight-channel adapter and JSON/CSV exports never claim physical firing", async () => {
  const demo = await syntheticDemo();
  const source = Object.fromEntries(CHANNELS.map(name => [name, { vector: [1, 2, 3], timestamp: 42 }]));
  const adapted = adaptSourceChannels(source);
  assert.deepEqual(adapted.channels.map(c => c.name), CHANNELS);
  assert.ok(adapted.channels.every(c => c.face === null));
  assert.deepEqual(adapted.sharedOrigin, MODEL.frame.origin);
  assert.throws(() => adaptSourceChannels({ ...source, extra: {} }));
  assert.throws(() => adaptSourceChannels({}));
  assert.equal(demo.synthetic, true);
  assert.equal(demo.genesisReceipt, null);
  assert.equal(demo.physicalConvergence, false);
  assert.equal(demo.frequency.physical, false);
  const csv = toCSV(demo);
  assert.equal(csv.trim().split("\n").length, 6);
  assert.ok(csv.includes(demo.cubeDigest) && csv.includes(demo.trajectoryDigest));
  assert.ok(csv.includes("cycles/synthetic-second"));
  const app = readFileSync(new URL("../backend/scandoc/app.js", import.meta.url), "utf8");
  for (const forbidden of ["fetch(", "XMLHttpRequest", "WebSocket", "localStorage", "burnModule"])
    assert.ok(!app.includes(forbidden));
});
