import { createHash } from "node:crypto";

/**
 * @typedef {Object} BurnEvent
 * @property {string} receiptCommitment
 * @property {string} previousEvent
 * @property {string} originCommitment
 * @property {"available→burned-origin"} transition
 * @property {"traversed"} gateway
 * @property {number} layer
 * @property {number} timestamp
 * @property {string} timestampProof
 */

export const BurnEvent = Object.freeze({
  required: Object.freeze([
    "receiptCommitment",
    "previousEvent",
    "originCommitment",
    "transition",
    "gateway",
    "layer",
    "timestamp",
    "timestampProof",
  ]),
  transition: "available→burned-origin",
  gateway: "traversed",
});

const STATE = {
  commitments: new Map(),
  burns: [],
  chainHead: null,
};

const sha512 = (input) => createHash("sha512").update(input).digest("hex");
const timestampProofFor = (id, timestamp) => sha512(`${id}:${timestamp}`);

export function registerCommitment(commitment) {
  if (
    commitment === null ||
    typeof commitment !== "object" ||
    typeof commitment.moduleId !== "string" ||
    !Number.isInteger(commitment.layer) ||
    commitment.layer < 0
  ) {
    throw new TypeError("Invalid commitment");
  }
  STATE.commitments.set(commitment.moduleId, {
    commitment,
    dependenciesResolved: false,
    executionStopped: false,
    capabilitiesRevoked: false,
  });
}

export function resolveCommitmentForBurn(id) {
  const record = STATE.commitments.get(id);
  if (!record || record.commitment.state === "burned") return null;
  record.dependenciesResolved = true;
  record.executionStopped = true;
  record.capabilitiesRevoked = true;
  return record;
}

export function markCommitmentBurned(id) {
  const record = STATE.commitments.get(id);
  if (record) record.commitment.state = "burned";
}

export function burnModule(id) {
  const record = STATE.commitments.get(id);
  if (!record || record.commitment.state === "burned") return null;
  if (
    !(
      record.dependenciesResolved &&
      record.executionStopped &&
      record.capabilitiesRevoked
    )
  ) {
    console.warn("Burn blocked: unresolved dependencies or active execution.");
    return null;
  }

  const commitment = record.commitment;
  const timestamp = Date.now();
  const burn = Object.freeze({
    receiptCommitment: commitment.moduleId,
    previousEvent: STATE.chainHead || "none",
    originCommitment: commitment.moduleId,
    transition: "available→burned-origin",
    gateway: "traversed",
    layer: commitment.layer,
    timestamp,
    timestampProof: timestampProofFor(commitment.moduleId, timestamp),
  });

  commitment.state = "burned";
  STATE.burns.push(burn);
  STATE.chainHead = burn.receiptCommitment;
  return burn;
}

export function verifyTimestampProof(event) {
  return (
    event !== null &&
    typeof event === "object" &&
    typeof event.receiptCommitment === "string" &&
    Number.isFinite(event.timestamp) &&
    typeof event.timestampProof === "string" &&
    event.timestampProof ===
      timestampProofFor(event.receiptCommitment, event.timestamp)
  );
}
