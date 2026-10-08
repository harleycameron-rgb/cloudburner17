import assert from "node:assert/strict";
import test from "node:test";
import { ingestTestResults } from "../src/ingest.js";
import {
  beginFeedCycle,
  canFeed,
  CLOUDBURNER17_ORCHESTRATE,
  harmoniseTriStream,
  proofRhythm,
  runtimeIgnition,
  stabiliseContradiction,
} from "../src/runtime.js";

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
  assert.equal(out.status, "IGNITION_STABLE");
});

test("runtime ignition detects drift when tests fail", () => {
  const out = runtimeIgnition([
    { name: "demo", ok: true },
    { name: "event-model", ok: false },
  ]);

  assert.equal(out.invariant, false);
  assert.equal(out.residue, 1);
  assert.equal(out.drift, 1);
  assert.equal(out.status, "IGNITION_VARIANT");
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
    status: "IGNITION_STABLE",
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

test("feed gate requires a non-empty stable ignition", () => {
  assert.equal(canFeed(runtimeIgnition([{ name: "healthy", ok: true }])), true);
  assert.equal(canFeed(runtimeIgnition([])), false);
  assert.equal(canFeed(runtimeIgnition([{ name: "failed", ok: false }])), false);
});

test("feed cycle activates stable batches and halts on drift", async () => {
  const active = await beginFeedCycle({
    pull: async () => [{ name: "healthy", ok: true }],
  });
  const halted = await beginFeedCycle({
    pull: async () => [{ name: "failed", ok: false }],
  });

  assert.equal(active.feed, "ACTIVE");
  assert.equal(active.invariant, true);
  assert.equal(active.truthVector.length, 1);
  assert.ok(active.timestamp > 0);
  assert.equal(halted.feed, "HALTED");
  assert.equal(halted.reason, "Invariant not stable");
  assert.equal(halted.ignition.residue, 1);
});

test("tri-stream and contradiction projections preserve source order", () => {
  const vector = [
    { name: "first", ok: true, timestamp: 1 },
    { name: "second", ok: false, timestamp: 2 },
  ];

  assert.deepEqual(harmoniseTriStream(vector), {
    publicStudy: [
      { name: "first", ok: true, pulse: "PUBLIC" },
      { name: "second", ok: false, pulse: "PUBLIC" },
    ],
    philosophicalReset: [
      { name: "first", ok: true, pulse: "PHILOSOPHICAL" },
      { name: "second", ok: false, pulse: "PHILOSOPHICAL" },
    ],
    businessProcedure: [
      { name: "first", ok: true, pulse: "BUSINESS" },
      { name: "second", ok: false, pulse: "BUSINESS" },
    ],
  });
  assert.deepEqual(stabiliseContradiction(vector), {
    contradictions: 1,
    stabilised: "TENSION_HELD",
    field: vector,
  });
});

test("proof rhythm marks origin and continuum without mutating input", () => {
  const vector = [
    { name: "first", ok: true, timestamp: 1 },
    { name: "second", ok: true, timestamp: 2 },
  ];

  assert.deepEqual(proofRhythm(vector), [
    { ...vector[0], rhythmIndex: 0, topology: "ORIGIN" },
    { ...vector[1], rhythmIndex: 1, topology: "CONTINUUM" },
  ]);
  assert.deepEqual(vector[0], { name: "first", ok: true, timestamp: 1 });
});

test("orchestration pulls once and exposes the complete runtime sequence", async () => {
  let pulls = 0;
  const result = await CLOUDBURNER17_ORCHESTRATE({
    pull: async () => {
      pulls += 1;
      return [{ name: "healthy", ok: true }];
    },
  });

  assert.equal(pulls, 1);
  assert.equal(result.ingestion.passed, 1);
  assert.equal(result.ignition.status, "IGNITION_STABLE");
  assert.equal(result.feedStatus, "FEED_OPEN");
  assert.equal(result.triStream.publicStudy[0].pulse, "PUBLIC");
  assert.equal(result.contradictionField.stabilised, "NO_TENSION");
  assert.equal(result.proofRhythm[0].topology, "ORIGIN");
  assert.equal(result.organismStatus, "ALIVE");
});

test("orchestration closes the feed for empty and failed batches", async () => {
  for (const batch of [[], [{ name: "failed", ok: false }]]) {
    const result = await CLOUDBURNER17_ORCHESTRATE({
      pull: async () => batch,
    });

    assert.equal(result.feedStatus, "FEED_CLOSED");
    assert.equal(result.organismStatus, "SLEEPING");
  }
});
