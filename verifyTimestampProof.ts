/* ========================================================================
   TIMESTAMP PROOF VERIFICATION — RFC3161 / OpenTimestamps Adapter (Stub)
   ======================================================================== */

export interface TimestampProof {
  proofId: string;
  commitmentHash: string;
  proofData: string;
  issuedAt: number;
  verifiedAt: number | null;
}

export interface TimestampVerificationResult {
  valid: boolean;
  reason: string;
  verifiedAt: number;
}

export function verifyTimestampProof(
  proof: TimestampProof,
  expectedCommitmentHash: string
): TimestampVerificationResult {
  if (!proof.proofId || !proof.commitmentHash || !proof.proofData) {
    return {
      valid: false,
      reason: "Malformed proof object",
      verifiedAt: Date.now()
    };
  }

  if (proof.commitmentHash !== expectedCommitmentHash) {
    return {
      valid: false,
      reason: "Commitment hash mismatch",
      verifiedAt: Date.now()
    };
  }

  return {
    valid: true,
    reason: "Stub verification passed",
    verifiedAt: Date.now()
  };
}
