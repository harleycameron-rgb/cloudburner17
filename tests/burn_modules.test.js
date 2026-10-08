import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import test from "node:test";
import {
  admitModule,
  burnModule as burnLifecycleModule,
  inspectHashDetails,
  reduceLifecycle,
  retireModule,
  verifyTimestampProof,
  generateSyntheticStateHash,
} from "../CLOUDBURNER17.js";
import { burnModule as burnById } from "../src/burn_logic.js";

const sha512 = (value) => createHash("sha512").update(value).digest("hex");

test("lifecycle reduction retains immutable ordered events", () => {
  const burn = {
    receiptCommitment: "receipt",
    originCommitment: "origin",
    transition: "available→burned-origin",
    layer: 1,
    timestamp: 100,
  };
  const first = reduceLifecycle(null, burn);
  const accepted = reduceLifecycle(first, {
    ...burn,
    transition: "destination-accepted",
    timestamp: 110,
    destinationAccepted: 109,
  });

  assert.equal(first.state, "burned-origin");
  assert.equal(accepted.acceptedAt, 109);
  assert.equal(accepted.events.length, 2);
  assert.equal(Object.isFrozen(accepted.events[0]), true);
  assert.equal(Object.isFrozen(accepted), true);
  assert.throws(
    () => reduceLifecycle(accepted, { ...burn, timestamp: 120 }),
    /append-only/,
  );
});

test("ID-based burn waits for retirement and verifies its timestamp proof", () => {
  const module = admitModule(`burn-${Date.now()}-${Math.random()}`, 2);
  assert.equal(burnById(module.moduleId), null);

  const dependency = module.moduleId;
  module.ancestry.push({ commitment: dependency });
  retireModule(module, [dependency]);
  const event = burnLifecycleModule(module.moduleId);

  assert.equal(event.receiptCommitment, module.moduleId);
  assert.equal(event.originCommitment, module.moduleId);
  assert.equal(verifyTimestampProof(event), true);
  assert.equal(verifyTimestampProof({ ...event, timestamp: event.timestamp + 1 }), false);
  assert.equal(burnById(module.moduleId), null);
});

test("synthetic state hash hashes averaged pixel values with SHA-512", () => {
  const result = generateSyntheticStateHash(
    { curvature: 2, potential: 4, tension: 6 },
    { curvature: 4, potential: 8, tension: 10 },
  );

  assert.equal(result.hash, sha512("3:6:8"));
  assert.equal(result.synthetic, true);
  assert.equal(result.qTrajectory.washburn, true);
  assert.equal(typeof result.qTrajectory.q, "number");
});

test("inspector maps hash, pixel, trajectory, and lifecycle fields", () => {
  const lifecycle = reduceLifecycle(null, {
    receiptCommitment: "receipt",
    originCommitment: "origin",
    transition: "available→burned-origin",
    layer: 0,
    timestamp: 123,
  });
  assert.deepEqual(
    inspectHashDetails(
      {
        hash: "abc",
        synthetic: true,
        qTrajectory: { q: 0.5 },
      },
      { curvature: 1, potential: 2, tension: 3 },
      lifecycle,
    ),
    {
      hash: "abc",
      syntheticHash: true,
      curvature: 1,
      potential: 2,
      tension: 3,
      qTrajectory: 0.5,
      lifecycle,
    },
  );
});
