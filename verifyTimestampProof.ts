/* ========================================================================
   TIMESTAMP PROOF VERIFICATION — RFC3161 / OpenTimestamps Adapter (Stub)
   ======================================================================== */

import { verifyTimestampProof as verifyStub } from "./src/timestamp_proof.js";

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
  return verifyStub(proof, expectedCommitmentHash);
}
