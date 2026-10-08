import { createHash } from "node:crypto";
import { burnModule, snapshot } from "./src/burn_logic.js";
import {
  admitModule,
  participateInConvergence,
  retireModule,
} from "./src/burn_lifecycle.js";
import { verifyTimestampProof } from "./src/timestamp_proof.js";

function computeTrajectory(payload) {
  const pixel = {
    curvature: Math.random(),
    potential: Math.random(),
    tension: Math.random(),
    timestamp: Date.now(),
  };
  const hash = createHash("sha512")
    .update(
      pixel.curvature.toString() +
        pixel.potential.toString() +
        pixel.tension.toString() +
        payload +
        pixel.timestamp.toString(),
    )
    .digest("hex");
  return {
    hash,
    synthetic: false,
    qTrajectory: { q: 0, timestamp: pixel.timestamp, washburn: false },
  };
}

export async function runBurnChainHarness(payload, layer = 1) {
  if (typeof payload !== "string" || payload.length === 0) {
    throw new TypeError("Payload must be a non-empty string");
  }
  if (!Number.isInteger(layer) || layer < 0) {
    throw new TypeError("Layer must be a non-negative integer");
  }

  console.log("🔥 Initiating Cloudburner17 burn-chain harness…");
  const topology = computeTrajectory(payload);
  console.log("Trajectory computed:", topology.hash);

  const module = admitModule(topology.hash, layer);
  participateInConvergence(module, [{ invariant: true, topology }]);
  retireModule(module, [module.moduleId]);
  const burnEvent = burnModule(module.moduleId);
  if (!burnEvent) {
    console.warn("Burn event failed or blocked.");
    return null;
  }
  console.log("Burn event:", burnEvent.transition);

  const proof = {
    proofId: `proof-${Date.now()}`,
    commitmentHash: burnEvent.receiptCommitment,
    proofData: "RFC3161-STUB",
    issuedAt: Date.now(),
    verifiedAt: null,
  };
  const verification = verifyTimestampProof(proof, burnEvent.receiptCommitment);
  console.log("Timestamp verification:", verification.reason);

  const state = snapshot();
  console.log("System snapshot:", state);
  return { payload, topology, burnEvent, proof, verification, state };
}
