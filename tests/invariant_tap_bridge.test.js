import assert from "node:assert/strict";
import test from "node:test";
import {
  bridgeInvariantTapToIgnition,
  runTapBridgeCycle,
} from "../CLOUDBURNER17.js";
import { runInvariantTapSession } from "../InvariantTap.js";

test("tap bridge converts ephemeral event names into ignition results", () => {
  const bridge = bridgeInvariantTapToIgnition(["alpha", "beta"]);

  assert.equal(bridge.status, "BRIDGE_ACTIVE");
  assert.equal(bridge.invariantPulse, true);
  assert.deepEqual(
    bridge.ignition.vector.map(({ name, ok }) => ({ name, ok })),
    [
      { name: "tap-alpha", ok: true },
      { name: "tap-beta", ok: true },
    ],
  );
  assert.equal(bridge.ingestion.invariantPulse, true);
});

test("tap bridge preserves failed event state and halts the feed cycle", async () => {
  const report = await runTapBridgeCycle({
    pull: async () => [
      { name: "alpha", ok: true },
      { name: "beta", ok: false },
    ],
  });

  assert.equal(report.feed, "HALTED");
  assert.equal(report.reason, "Invariant mismatch detected");
  assert.equal(report.bridge.invariantPulse, false);
  assert.equal(report.bridge.ignition.residue, 1);
});

test("tap bridge opens a cycle for passing events", async () => {
  const report = await runTapBridgeCycle({
    pull: async () => ["alpha"],
  });

  assert.equal(report.feed, "ACTIVE");
  assert.equal(report.bridge.invariantPulse, true);
  assert.ok(report.timestamp > 0);
});

test("tap sessions reject malformed events and non-array inputs", () => {
  assert.throws(() => runInvariantTapSession("alpha"), TypeError);
  assert.throws(() => runInvariantTapSession([null]), TypeError);
  assert.throws(
    () => runInvariantTapSession([{ name: "alpha", ok: "true" }]),
    TypeError,
  );
});
