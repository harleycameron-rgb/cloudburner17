import { createHash } from "node:crypto";
import {
  burnModule as executeBurnModule,
  markCommitmentBurned,
  registerCommitment,
  resolveCommitmentForBurn,
} from "./burn_logic.js";

/**
 * @typedef {Object} LifecycleEventShape
 * @property {string} receiptCommitment
 * @property {string} originCommitment
 * @property {"available→burned-origin" | "destination-accepted" | "externally-timestamped"} transition
 * @property {number} layer
 * @property {number} timestamp
 * @property {number} [destinationAccepted]
 * @property {string} [timestampProof]
 */

export const LifecycleEventShape = Object.freeze({
  required: Object.freeze([
    "receiptCommitment",
    "originCommitment",
    "transition",
    "layer",
    "timestamp",
  ]),
  transitions: Object.freeze([
    "available→burned-origin",
    "destination-accepted",
    "externally-timestamped",
  ]),
  optional: Object.freeze(["destinationAccepted", "timestampProof"]),
});

export class ReceiptLifecycle {
  constructor(values = {}) {
    this.receiptCommitment = values.receiptCommitment ?? null;
    this.originCommitment = values.originCommitment ?? null;
    this.createdAt = values.createdAt ?? null;
    this.burnedAt = values.burnedAt ?? null;
    this.acceptedAt = values.acceptedAt ?? null;
    this.timestampProof = values.timestampProof ?? null;
    this.state = values.state ?? "available";
    this.gateway = values.gateway ?? "untraversed";
    this.events = Object.freeze([...(values.events ?? [])]);
    Object.freeze(this);
  }
}

function validateLifecycleEvent(event) {
  if (
    event === null ||
    typeof event !== "object" ||
    typeof event.receiptCommitment !== "string" ||
    event.receiptCommitment.length === 0 ||
    typeof event.originCommitment !== "string" ||
    event.originCommitment.length === 0 ||
    !LifecycleEventShape.transitions.includes(event.transition) ||
    !Number.isInteger(event.layer) ||
    event.layer < 0 ||
    !Number.isFinite(event.timestamp) ||
    (event.destinationAccepted !== undefined &&
      !Number.isFinite(event.destinationAccepted)) ||
    (event.timestampProof !== undefined &&
      typeof event.timestampProof !== "string")
  ) {
    throw new TypeError("Invalid lifecycle event");
  }
}

export function reduceLifecycle(previous, event) {
  validateLifecycleEvent(event);
  const lifecycle =
    previous === null || previous === undefined
      ? new ReceiptLifecycle()
      : previous;
  if (!(lifecycle instanceof ReceiptLifecycle)) {
    throw new TypeError("Previous lifecycle must be a ReceiptLifecycle");
  }
  if (
    lifecycle.receiptCommitment !== null &&
    (lifecycle.receiptCommitment !== event.receiptCommitment ||
      lifecycle.originCommitment !== event.originCommitment)
  ) {
    throw new Error("Lifecycle commitment cannot change");
  }
  const lastEvent = lifecycle.events.at(-1);
  if (lastEvent && event.timestamp < lastEvent.timestamp) {
    throw new Error("Lifecycle events must be timestamp ordered");
  }
  if (
    (event.transition === "available→burned-origin" &&
      lifecycle.burnedAt !== null) ||
    (event.transition === "destination-accepted" &&
      lifecycle.acceptedAt !== null)
  ) {
    throw new Error("Lifecycle transition is append-only");
  }

  const immutableEvent = Object.freeze({
    receiptCommitment: event.receiptCommitment,
    originCommitment: event.originCommitment,
    transition: event.transition,
    layer: event.layer,
    timestamp: event.timestamp,
    ...(event.destinationAccepted === undefined
      ? {}
      : { destinationAccepted: event.destinationAccepted }),
    ...(event.timestampProof === undefined
      ? {}
      : { timestampProof: event.timestampProof }),
  });
  const values = {
    receiptCommitment: event.receiptCommitment,
    originCommitment: event.originCommitment,
    createdAt: lifecycle.createdAt ?? event.timestamp,
    burnedAt: lifecycle.burnedAt,
    acceptedAt: lifecycle.acceptedAt,
    timestampProof: lifecycle.timestampProof,
    state: lifecycle.state,
    gateway: lifecycle.gateway,
    events: [...lifecycle.events, immutableEvent],
  };
  if (event.transition === "available→burned-origin") {
    values.state = "burned-origin";
    values.gateway = "traversed";
    values.burnedAt = event.timestamp;
  } else if (event.transition === "destination-accepted") {
    values.state = "destination-accepted";
    values.acceptedAt = event.destinationAccepted ?? event.timestamp;
  } else {
    values.state = "externally-timestamped";
    values.timestampProof = event.timestampProof ?? null;
  }
  return new ReceiptLifecycle(values);
}

/**
 * @typedef {Object} BurnEvent
 * @property {string} receiptCommitment
 * @property {string} previousEvent
 * @property {string} originCommitment
 * @property {"available→burned-origin"} transition
 * @property {"traversed"} gateway
 * @property {number} layer
 * @property {number} [timestamp]
 */

function sha512(input) {
  return createHash("sha512").update(input).digest("hex");
}

function assertModule(module) {
  if (
    module === null ||
    typeof module !== "object" ||
    typeof module.moduleId !== "string" ||
    !Array.isArray(module.ancestry)
  ) {
    throw new TypeError("Invalid admitted module");
  }
}

export function admitModule(receiptCommitment, layer) {
  if (typeof receiptCommitment !== "string" || receiptCommitment.length === 0) {
    throw new TypeError("Receipt commitment must be a non-empty string");
  }
  if (!Number.isInteger(layer) || layer < 0) {
    throw new TypeError("Layer must be a non-negative integer");
  }

  const module = {
    moduleId: receiptCommitment,
    layer,
    state: "admitted",
    ancestry: [],
    admittedAt: Date.now(),
  };
  registerCommitment(module);
  return module;
}

export function participateInConvergence(module, convergenceVector) {
  assertModule(module);
  if (module.state !== "admitted") {
    throw new Error("Convergence requires an admitted module");
  }
  if (
    !Array.isArray(convergenceVector) ||
    convergenceVector.some(
      (entry) =>
        entry === null ||
        typeof entry !== "object" ||
        typeof entry.invariant !== "boolean",
    )
  ) {
    throw new TypeError("Convergence vector entries must have a boolean invariant");
  }

  module.ancestry.push({
    commitment: module.moduleId,
    vector: structuredClone(convergenceVector),
    time: Date.now(),
  });

  return convergenceVector.some((entry) => entry.invariant === false)
    ? "fail"
    : "ok";
}

export function retireModule(module, dependencies) {
  assertModule(module);
  if (module.state !== "admitted") {
    throw new Error("Retirement requires an admitted module");
  }
  if (
    !Array.isArray(dependencies) ||
    dependencies.some((dependency) => typeof dependency !== "string")
  ) {
    throw new TypeError("Dependencies must be an array of commitment strings");
  }

  const unsatisfied = dependencies.filter(
    (dependency) =>
      !module.ancestry.some((entry) => entry.commitment === dependency),
  );
  if (unsatisfied.length > 0) {
    throw new Error("Retirement blocked: dependency ancestry incomplete");
  }

  module.state = "retired";
  module.executionRevoked = true;
  resolveCommitmentForBurn(module.moduleId);
  return module;
}

export function burnModule(module, chainHead) {
  if (typeof module === "string") {
    return executeBurnModule(module);
  }
  assertModule(module);
  if (module.state !== "retired") {
    throw new Error("Burn requires prior retirement");
  }
  if (typeof chainHead !== "string") {
    throw new TypeError("Chain head must be a string");
  }

  const originCommitment = sha512(`${module.moduleId}::origin`);
  const burnEvent = {
    receiptCommitment: module.moduleId,
    previousEvent: chainHead,
    originCommitment,
    transition: "available→burned-origin",
    gateway: "traversed",
    layer: module.layer,
    timestamp: Date.now(),
  };
  const newChainHead = sha512(JSON.stringify(burnEvent));

  module.state = "burned";
  module.origin = originCommitment;
  module.chainHead = newChainHead;
  markCommitmentBurned(module.moduleId);

  return { burnEvent, newChainHead };
}

export function revokeToOrigin(module) {
  assertModule(module);
  if (module.state !== "burned" || typeof module.origin !== "string") {
    throw new Error("Revocation requires a burned module");
  }

  return {
    origin: module.origin,
    revokedAt: Date.now(),
    note: "Trajectory preserved; identity ended; origin retained",
  };
}

export function trajectoryStream(module) {
  assertModule(module);
  return module.ancestry.map((entry) => ({
    commitment: entry.commitment,
    time: entry.time,
    vector: structuredClone(entry.vector),
  }));
}
