/* TIMESTAMP PROOF VERIFICATION — RFC3161 / OpenTimestamps Adapter (Stub) */

export function verifyTimestampProof(proof, expectedCommitmentHash) {
  if (
    proof === null ||
    typeof proof !== "object" ||
    typeof proof.proofId !== "string" ||
    !proof.proofId ||
    typeof proof.commitmentHash !== "string" ||
    !proof.commitmentHash ||
    typeof proof.proofData !== "string" ||
    !proof.proofData
  ) {
    return {
      valid: false,
      reason: "Malformed proof object",
      verifiedAt: Date.now(),
    };
  }

  if (proof.commitmentHash !== expectedCommitmentHash) {
    return {
      valid: false,
      reason: "Commitment hash mismatch",
      verifiedAt: Date.now(),
    };
  }

  return {
    valid: true,
    reason: "Stub verification passed",
    verifiedAt: Date.now(),
  };
}
