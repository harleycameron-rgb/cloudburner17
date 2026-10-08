import { createHash } from "node:crypto";

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

  return {
    moduleId: receiptCommitment,
    layer,
    state: "admitted",
    ancestry: [],
    admittedAt: Date.now(),
  };
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
    vector: convergenceVector.map((entry) => ({ ...entry })),
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
  return module;
}

export function burnModule(module, chainHead) {
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
    vector: entry.vector.map((item) => ({ ...item })),
  }));
}
