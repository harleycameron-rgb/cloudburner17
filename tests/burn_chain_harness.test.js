import assert from "node:assert/strict";
import test from "node:test";
import {
  runBurnChainHarness,
  snapshot,
  verifyTimestampProof as verifyBurnTimestamp,
} from "../CLOUDBURNER17.js";
import { burnModule } from "../src/burn_logic.js";
import { verifyTimestampProof } from "../src/timestamp_proof.js";

test("burn-chain harness executes the full lifecycle", async () => {
  const result = await runBurnChainHarness("payload-test");

  assert.ok(result);
  assert.equal(result.payload, "payload-test");
  assert.match(result.topology.hash, /^[a-f0-9]{128}$/);
  assert.equal(result.topology.synthetic, false);
  assert.equal(result.burnEvent.receiptCommitment, result.topology.hash);
  assert.equal(result.burnEvent.transition, "available→burned-origin");
  assert.equal(result.burnEvent.layer, 1);
  assert.equal(verifyBurnTimestamp(result.burnEvent), true);
  assert.equal(result.proof.commitmentHash, result.burnEvent.receiptCommitment);
  assert.equal(result.proof.proofData, "RFC3161-STUB");
  assert.equal(result.verification.valid, true);
  assert.equal(result.verification.reason, "Stub verification passed");
  assert.equal(typeof result.verification.verifiedAt, "number");
  assert.equal(result.state.chainHead, result.burnEvent.receiptCommitment);
  assert.deepEqual(result.state.burns.at(-1), result.burnEvent);
  const module = result.state.commitments.find(
    (entry) => entry.moduleId === result.burnEvent.receiptCommitment,
  );
  assert.equal(module.state, "burned");
  assert.equal(module.executionRevoked, true);
  assert.deepEqual(module.ancestry[0].vector, [
    { invariant: true, topology: result.topology },
  ]);
  assert.equal(burnModule(module.moduleId), null);
});

test("repeat cycles honor layers, link burns, and return detached snapshots", async () => {
  const first = await runBurnChainHarness("repeat-payload", 0);
  const second = await runBurnChainHarness("repeat-payload", 3);

  assert.equal(first.burnEvent.layer, 0);
  assert.equal(second.burnEvent.layer, 3);
  assert.notEqual(first.topology.hash, second.topology.hash);
  assert.equal(second.burnEvent.previousEvent, first.burnEvent.receiptCommitment);
  assert.equal(second.state.burns.length, first.state.burns.length + 1);
  assert.equal(first.state.chainHead, first.burnEvent.receiptCommitment);

  second.state.burns.at(-1).transition = "tampered";
  second.state.commitments.at(-1).ancestry[0].vector[0].invariant = false;
  const current = snapshot();
  assert.equal(current.burns.at(-1).transition, "available→burned-origin");
  assert.equal(current.commitments.at(-1).ancestry[0].vector[0].invariant, true);
});

test("invalid harness inputs do not change system state", async () => {
  const before = snapshot();
  for (const payload of ["", null, undefined, 42, {}]) {
    await assert.rejects(runBurnChainHarness(payload), TypeError);
  }
  for (const layer of [-1, 1.5, NaN, Infinity, "1", null]) {
    await assert.rejects(runBurnChainHarness("payload-test", layer), TypeError);
  }
  assert.deepEqual(snapshot(), before);
});

test("timestamp adapter rejects malformed proofs and commitment mismatches", () => {
  for (const proof of [null, undefined, {}, { proofId: 1 }]) {
    const result = verifyTimestampProof(proof, "receipt");
    assert.equal(result.valid, false);
    assert.equal(result.reason, "Malformed proof object");
    assert.equal(typeof result.verifiedAt, "number");
  }
  const proof = {
    proofId: "proof-test",
    commitmentHash: "wrong-receipt",
    proofData: "RFC3161-STUB",
    issuedAt: Date.now(),
    verifiedAt: null,
  };
  assert.equal(
    verifyTimestampProof(proof, "receipt").reason,
    "Commitment hash mismatch",
  );
});
