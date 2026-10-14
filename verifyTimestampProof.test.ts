import { describe, test } from "node:test";
import assert from "node:assert/strict";
import { verifyTimestampProof } from "./verifyTimestampProof.ts";
import type { TimestampProof } from "./verifyTimestampProof.ts";

describe("verifyTimestampProof()", () => {
  test("accepts a valid proof with matching commitment hash", () => {
    const proof: TimestampProof = {
      proofId: "proof-001",
      commitmentHash: "abc123",
      proofData: "DER-BLOB",
      issuedAt: Date.now(),
      verifiedAt: null
    };

    const result = verifyTimestampProof(proof, "abc123");

    assert.equal(result.valid, true);
    assert.equal(result.reason, "Stub verification passed");
    assert.equal(typeof result.verifiedAt, "number");
  });

  test("rejects malformed proof objects", () => {
    const malformed: TimestampProof = {
      proofId: "",
      commitmentHash: "",
      proofData: "",
      issuedAt: Date.now(),
      verifiedAt: null
    };

    const result = verifyTimestampProof(malformed, "abc123");

    assert.equal(result.valid, false);
    assert.equal(result.reason, "Malformed proof object");
  });

  test("rejects proof when commitment hash does not match", () => {
    const proof: TimestampProof = {
      proofId: "proof-002",
      commitmentHash: "wrongHash",
      proofData: "DER-BLOB",
      issuedAt: Date.now(),
      verifiedAt: null
    };

    const result = verifyTimestampProof(proof, "expectedHash");

    assert.equal(result.valid, false);
    assert.equal(result.reason, "Commitment hash mismatch");
  });

  test("verifiedAt is always populated", () => {
    const proof: TimestampProof = {
      proofId: "proof-003",
      commitmentHash: "abc123",
      proofData: "DER-BLOB",
      issuedAt: Date.now(),
      verifiedAt: null
    };

    const result = verifyTimestampProof(proof, "abc123");

    assert.equal(typeof result.verifiedAt, "number");
  });
});
