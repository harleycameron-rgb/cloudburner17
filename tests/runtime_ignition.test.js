import assert from "node:assert/strict";
import test from "node:test";
import { ingestTestResults } from "../src/ingest.js";
import { runtimeIgnition } from "../src/runtime.js";

test("ingests basic test results", () => {
  const out = ingestTestResults([
    { name: "alpha", ok: true },
    { name: "beta", ok: false },
  ]);

  assert.equal(out.passed, 1);
  assert.equal(out.failed, 1);
  assert.equal(out.invariantPulse, false);
  assert.equal(out.vector.length, 2);
});

test("runtime ignition preserves invariant when all tests pass", () => {
  const out = runtimeIgnition([
    { name: "demo", ok: true },
    { name: "event-model", ok: true },
  ]);

  assert.equal(out.invariant, true);
  assert.equal(out.residue, 0);
  assert.equal(out.drift, 0);
  assert.equal(out.status, "IGNITION_READY");
});

test("runtime ignition detects drift when tests fail", () => {
  const out = runtimeIgnition([
    { name: "demo", ok: true },
    { name: "event-model", ok: false },
  ]);

  assert.equal(out.invariant, false);
  assert.equal(out.residue, 1);
  assert.equal(out.drift, 1);
  assert.equal(out.status, "IGNITION_DRIFT");
});

test("truth-vector shape is correct for tri-stream harmonisation", () => {
  const out = runtimeIgnition([
    { name: "public-study", ok: true },
    { name: "philosophical-reset", ok: true },
    { name: "business-procedure", ok: true },
  ]);

  assert.equal(out.vector.length, 3);
  for (const entry of out.vector) {
    assert.deepEqual(Object.keys(entry), ["name", "ok", "timestamp"]);
    assert.equal(typeof entry.name, "string");
    assert.equal(typeof entry.ok, "boolean");
    assert.equal(Number.isInteger(entry.timestamp), true);
  }
});

test("invariant axis remains readable from all sides", () => {
  const out = runtimeIgnition([
    { name: "north", ok: true },
    { name: "south", ok: true },
    { name: "east", ok: true },
    { name: "west", ok: true },
  ]);

  assert.equal(out.invariant, true);
  assert.equal(out.vector.every((entry) => entry.ok), true);
});

test("compassion invariant holds even with mixed results", () => {
  const out = runtimeIgnition([
    { name: "core-ethic", ok: true },
    { name: "stress-case", ok: false },
  ]);

  assert.equal(out.vector.length, 2);
  assert.equal(typeof out.status, "string");
});

test("each fragment behaves as a complete miniature system", () => {
  const out = runtimeIgnition([{ name: "fragment-A", ok: true }]);

  assert.equal(out.vector.length, 1);
  assert.equal(out.invariant, true);
});

test("proof behaves as a rhythm, not a result", () => {
  const out = runtimeIgnition([
    { name: "pulse-1", ok: true },
    { name: "pulse-2", ok: true },
    { name: "pulse-3", ok: true },
  ]);

  assert.equal(out.vector.length, 3);
  assert.equal(out.invariant, true);
});

test("contradiction stabilises the system rather than breaking it", () => {
  const out = runtimeIgnition([
    { name: "harmonic-A", ok: true },
    { name: "harmonic-B", ok: false },
  ]);

  assert.equal(out.residue, 1);
  assert.equal(out.drift, 1);
  assert.equal(out.vector.length, 2);
});

test("time behaves as a topology, not a line", () => {
  const out = runtimeIgnition([
    { name: "t0", ok: true },
    { name: "t1", ok: true },
  ]);
  const timestamps = out.vector.map((entry) => entry.timestamp);

  assert.ok(timestamps[0] > 0);
  assert.ok(timestamps[1] >= timestamps[0]);
});

test("empty input has no failures or drift", () => {
  assert.deepEqual(ingestTestResults([]), {
    passed: 0,
    failed: 0,
    invariantPulse: true,
    vector: [],
  });
  assert.deepEqual(runtimeIgnition([]), {
    status: "IGNITION_READY",
    invariant: true,
    residue: 0,
    drift: 0,
    vector: [],
  });
});

test("all failures are counted and calls remain independent", () => {
  const results = [
    { name: "failure-A", ok: false },
    { name: "failure-B", ok: false },
    { name: "failure-C", ok: false },
  ];
  const ingested = ingestTestResults(results);
  const out = runtimeIgnition(results);

  assert.equal(ingested.passed, 0);
  assert.equal(ingested.failed, 3);
  assert.equal(ingested.invariantPulse, false);
  assert.equal(out.invariant, false);
  assert.equal(out.residue, 3);
  assert.equal(out.drift, 3);
  assert.equal(runtimeIgnition([{ name: "next", ok: true }]).invariant, true);
});

test("ingestion preserves order and does not mutate or retain input records", () => {
  const results = Object.freeze([
    Object.freeze({ name: "duplicate", ok: true, timestamp: -1 }),
    Object.freeze({ name: "duplicate", ok: false }),
  ]);
  const out = runtimeIgnition(results);

  assert.deepEqual(
    out.vector.map(({ name, ok }) => ({ name, ok })),
    [
      { name: "duplicate", ok: true },
      { name: "duplicate", ok: false },
    ],
  );
  assert.notEqual(out.vector, results);
  assert.notEqual(out.vector[0], results[0]);
  assert.ok(out.vector[0].timestamp > 0);
  out.vector[0].ok = false;
  assert.equal(results[0].ok, true);
});

test("malformed inputs are rejected rather than producing a false invariant", () => {
  const invalid = [
    undefined,
    null,
    {},
    "results",
    [null],
    [undefined],
    [1],
    [{}],
    [{ name: 1, ok: true }],
    [{ name: "missing-ok" }],
    [{ name: "truthy", ok: "false" }],
    new Array(1),
  ];

  for (const results of invalid) {
    assert.throws(() => ingestTestResults(results), TypeError);
    assert.throws(() => runtimeIgnition(results), TypeError);
  }
});
