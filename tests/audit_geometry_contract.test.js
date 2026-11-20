import assert from "node:assert/strict";
import test from "node:test";
import "../backend/portal/audit/web/geometry.js";
import "../backend/portal/audit/web/protocol.js";

const G = globalThis.TentacledGeometry;
const P = globalThis.TentacledProtocol;

function fixture() {
  return {
    units: "diagnostic-unit",
    origin: [0.2, -0.3, 0.4],
    points: [
      { id: "tap", position: [1.2, 0.1, 0.3] },
      { id: "surface", position: [-0.2, 1.3, 0.4] },
      { id: "gain", position: [-1.1, -0.4, 0.8] },
      { id: "engine", position: [0.2, -1, -0.3] },
    ],
    edges: [["tap", "surface"], ["surface", "gain"], ["gain", "engine"]],
  };
}

function transform(cloud, pointTransform, originTransform = pointTransform) {
  return {
    ...cloud,
    origin: originTransform(cloud.origin),
    points: cloud.points.map((point) => ({
      ...point,
      position: pointTransform(point.position),
    })),
    edges: cloud.edges.map((edge) => [...edge]),
  };
}

function rotate(point) {
  return G.rotateX(G.rotateZ(point, 0.37), -0.22);
}

function translate(point, offset) {
  return point.map((coordinate, axis) => coordinate + offset[axis]);
}

function metric(cloud) {
  return G.comparePointClouds(cloud, cloud);
}

test("rigid rotation and joint origin/geometry translations preserve measured relations", async () => {
  const before = fixture();
  const rotation = transform(before, rotate);
  const translation = transform(
    before,
    (point) => translate(point, [12, -5, 2]),
  );
  for (const after of [rotation, translation]) {
    const result = G.comparePointClouds(before, after);
    assert.equal(result.units, "diagnostic-unit");
    assert.equal(result.topologyPreserved, true);
    assert.equal(result.maxRadialError < 1e-12, true);
    assert.equal(result.maxPairwiseDistanceChange < 1e-12, true);
    assert.notEqual(await P.sha512(before), await P.sha512(after));
  }
});

test("reordered records and undirected edges preserve keyed metrics but not exact record digest", async () => {
  const before = fixture();
  const after = {
    ...before,
    points: [...before.points].reverse(),
    edges: before.edges.map(([left, right]) => [right, left]).reverse(),
  };
  assert.deepEqual(G.comparePointClouds(before, after), metric(before));
  assert.notEqual(await P.sha512(before), await P.sha512(after));
});

test("reflection preserves radii and distances but reverses oriented volume and record identity", async () => {
  const before = fixture();
  const after = transform(before, ([x, y, z]) => [-x, y, z]);
  const result = G.comparePointClouds(before, after);
  assert.equal(result.maxRadialError, 0);
  assert.equal(result.maxPairwiseDistanceChange, 0);
  assert.equal(result.topologyPreserved, true);
  const determinant = (a, b, c) =>
    a[0] * (b[1] * c[2] - b[2] * c[1]) -
    a[1] * (b[0] * c[2] - b[2] * c[0]) +
    a[2] * (b[0] * c[1] - b[1] * c[0]);
  const relative = (cloud) => cloud.points.slice(1, 4).map(({ position }) =>
    position.map((value, axis) => value - cloud.points[0].position[axis]));
  assert.ok(determinant(...relative(before)) * determinant(...relative(after)) < 0);
  assert.notEqual(await P.sha512(before), await P.sha512(after));
});

test("a local surface twist can preserve a radius while changing pairwise distances", () => {
  const before = fixture();
  const after = structuredClone(before);
  const twisted = after.points.find((point) => point.id === "gain");
  twisted.position = G.rotateZ(
    twisted.position.map((value, axis) => value - after.origin[axis]),
    0.31,
  ).map((value, axis) => value + after.origin[axis]);
  const result = G.comparePointClouds(before, after);
  assert.equal(result.topologyPreserved, true);
  assert.equal(result.maxRadialError < 1e-12, true);
  assert.equal(result.maxPairwiseDistanceChange > 0, true);
});

test("connectivity changes are reported separately from unchanged geometry", async () => {
  const before = fixture();
  const after = { ...before, edges: [["tap", "surface"], ["surface", "engine"]] };
  const result = G.comparePointClouds(before, after);
  assert.equal(result.maxRadialError, 0);
  assert.equal(result.maxPairwiseDistanceChange, 0);
  assert.equal(result.topologyPreserved, false);
  assert.deepEqual(result.changedConnectivityEdges, [
    { edge: ["engine", "gain"], change: "removed" },
    { edge: ["engine", "surface"], change: "added" },
    { edge: ["gain", "surface"], change: "removed" },
  ]);
  assert.notEqual(await P.sha512(before), await P.sha512(after));
});

test("unsupplied connectivity stays explicitly unmeasured", () => {
  const { edges, ...before } = fixture();
  const after = structuredClone(before);
  const result = G.comparePointClouds(before, after);
  assert.equal(result.topologyPreserved, null);
  assert.equal(result.changedConnectivityEdges, null);
});

test("changed identities are reported without fabricating matched geometry metrics", () => {
  const before = fixture();
  const after = structuredClone(before);
  after.points[3].id = "foretentacle";
  after.edges[2] = ["gain", "foretentacle"];
  const result = G.comparePointClouds(before, after);
  assert.deepEqual(result.missingBefore, ["foretentacle"]);
  assert.deepEqual(result.missingAfter, ["engine"]);
  assert.ok(Number.isFinite(result.maxRadialError));
  assert.equal(result.pairwiseDistanceChanges.length, 3);
  assert.equal(result.topologyPreserved, false);
});

test("point-cloud comparison does not mutate caller-owned records", () => {
  const before = fixture();
  const after = transform(before, rotate);
  const snapshot = JSON.stringify([before, after]);
  G.comparePointClouds(before, after);
  assert.equal(JSON.stringify([before, after]), snapshot);
});

test("malformed, empty, non-finite, sparse, and mismatched-unit clouds fail closed", () => {
  const base = fixture();
  for (const cloud of [
    null,
    { ...base, points: [] },
    { ...base, origin: [0, 0] },
    { ...base, origin: [0, NaN, 0] },
    { ...base, points: [{ id: "sparse", position: [1, , 0] }] },
    { ...base, points: [...base.points, base.points[0]] },
    { ...base, edges: [["tap", "unknown"]] },
    { ...base, edges: [["tap", "tap"]] },
    { ...base, edges: [["tap", ,]] },
    { ...base, edges: [["tap", "surface"], ["surface", "tap"]] },
    { ...base, points: Array.from({ length: 65 }, (_, index) => ({
      id: `point-${index}`, position: [index, 0, 0],
    })) },
  ]) {
    assert.throws(() => G.comparePointClouds(base, cloud));
  }
  const huge = {
    units: "large-unit",
    origin: [0, 0, 0],
    points: [
      { id: "left", position: [-1e308, 0, 0] },
      { id: "right", position: [1e308, 0, 0] },
    ],
    edges: [],
  };
  assert.throws(() => G.comparePointClouds(huge, huge), RangeError);
  assert.throws(() =>
    G.comparePointClouds(base, { ...base, units: "other-unit" }));
  assert.throws(() => G.comparePointClouds(base, { ...base, units: "" }));
});

test("repeated inverse transform cycles remain within a declared numerical sensitivity bound", () => {
  const before = fixture();
  let after = structuredClone(before);
  for (let cycle = 0; cycle < 100; cycle += 1) {
    after = transform(after, (point) => G.rotateZ(point, 1e-3));
    after = transform(after, (point) => G.rotateZ(point, -1e-3));
  }
  const result = G.comparePointClouds(before, after);
  assert.ok(result.maxRadialError <= 1e-12);
  assert.ok(result.maxPairwiseDistanceChange <= 1e-12);
  const injected = structuredClone(before);
  injected.points[0].position[0] += 5e-12;
  const injectedResult = G.comparePointClouds(before, injected);
  assert.ok(injectedResult.maxRadialError > 1e-12);
  assert.ok(injectedResult.maxRadialError < 1e-10);
});
