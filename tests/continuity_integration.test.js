import assert from "node:assert/strict";
import test from "node:test";
import {
  CLOUDBURNER17_ORCHESTRATE,
  continuityLoop,
  safeFeed,
} from "../CLOUDBURNER17.js";

test("continuity helpers compose with the public orchestrator and pull once per pulse", async () => {
  const realNow = Date.now;
  const realSetTimeout = globalThis.setTimeout;
  const realLog = console.log;
  let now = 10_000;
  let pulls = 0;
  let batch = [{ name: "healthy", ok: true }];
  const messages = [];
  const source = {
    pull: async () => {
      pulls += 1;
      return batch;
    },
  };
  Date.now = () => now;

  try {
    const first = await safeFeed(source, CLOUDBURNER17_ORCHESTRATE);
    assert.equal(first.status, "SAFE_UPDATE");
    assert.equal(first.report.organismStatus, "ALIVE");
    assert.equal(pulls, 1);

    now += 149;
    assert.equal(
      (await safeFeed(source, CLOUDBURNER17_ORCHESTRATE)).status,
      "HALTED",
    );
    assert.equal(pulls, 2);

    now += 150;
    batch = [{ name: "failed", ok: false }];
    assert.equal(
      (await safeFeed(source, CLOUDBURNER17_ORCHESTRATE)).status,
      "HALTED",
    );
    assert.equal(pulls, 3);

    now += 150;
    batch = [{ name: "healthy", ok: true }];
    console.log = (...args) => messages.push(args);
    globalThis.setTimeout = (callback, delay) => {
      assert.equal(delay, 150);
      now += delay;
      batch = [];
      callback();
      return 0;
    };
    await continuityLoop(source, CLOUDBURNER17_ORCHESTRATE);

    assert.equal(pulls, 5);
    assert.deepEqual(messages, [
      ["SAFE PULSE:", "ALIVE"],
      ["SAFETY HALT:", "Continuity violation detected"],
    ]);
  } finally {
    Date.now = realNow;
    globalThis.setTimeout = realSetTimeout;
    console.log = realLog;
  }
});
