import {
  verifyTimestampProof,
  TimestampProof
} from "./verifyTimestampProof";

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

    expect(result.valid).toBe(true);
    expect(result.reason).toBe("Stub verification passed");
    expect(typeof result.verifiedAt).toBe("number");
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

    expect(result.valid).toBe(false);
    expect(result.reason).toBe("Malformed proof object");
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

    expect(result.valid).toBe(false);
    expect(result.reason).toBe("Commitment hash mismatch");
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

    expect(typeof result.verifiedAt).toBe("number");
  });
});
