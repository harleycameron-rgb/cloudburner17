import assert from "node:assert/strict";
import test from "node:test";
import {
  LAUNCH_ROLES,
  validateHash1536Readiness,
} from "../CLOUDBURNER17.js";

function validReadiness() {
  return {
    kind: "COORDINATED_SIX_LEG_LAUNCH",
    eventName: "hash1536",
    phase: "READINESS_ONLY",
    liveGate: "CLOSED",
    geometryReference: [1024, 1024, 0],
    roles: LAUNCH_ROLES.map((role, logicalTick) => ({
      role,
      logicalTick,
      measurement: null,
    })),
    qualification: { status: "UNRESOLVED", authorized: false },
  };
}

test("accepts the exact six launch roles with unresolved values and a closed gate", () => {
  const contract = validReadiness();

  assert.equal(validateHash1536Readiness(contract), true);
  assert.deepEqual(contract.geometryReference, [1024, 1024, 0]);
  assert.equal(contract.roles.every(({ measurement }) => measurement === null), true);
});

test("rejects either post-launch extension as a launch contract", () => {
  for (const extension of [
    {
      kind: "POST_LAUNCH_EXTENSION",
      extension: "RETROSPECTIVE_TEMPORAL",
      linkedTo: "Sentinel",
    },
    {
      kind: "POST_LAUNCH_EXTENSION",
      extension: "FORWARD_DECONSTRUCTIVE",
      boundedBy: "PRESENT",
    },
  ]) {
    assert.equal(validateHash1536Readiness(extension), false);
  }
});

test("rejects missing, duplicate, and unknown launch roles", () => {
  const missing = validReadiness();
  missing.roles.pop();
  assert.equal(validateHash1536Readiness(missing), false);

  const duplicate = validReadiness();
  duplicate.roles[5].role = "TAP";
  assert.equal(validateHash1536Readiness(duplicate), false);

  const unknown = validReadiness();
  unknown.roles[5].role = "SCIENCE";
  assert.equal(validateHash1536Readiness(unknown), false);
});

test("rejects invalid logical ticks", () => {
  for (const logicalTick of [-1, 1.5, Number.NaN, Number.POSITIVE_INFINITY, Number.MAX_SAFE_INTEGER + 1]) {
    const contract = validReadiness();
    contract.roles[0].logicalTick = logicalTick;
    assert.equal(validateHash1536Readiness(contract), false);
  }
});

test("rejects nonfinite measurements and reference coordinates", () => {
  for (const measurement of [Number.NaN, Number.POSITIVE_INFINITY, Number.NEGATIVE_INFINITY]) {
    const contract = validReadiness();
    contract.roles[0].measurement = measurement;
    assert.equal(validateHash1536Readiness(contract), false);
  }

  const invalidReference = validReadiness();
  invalidReference.geometryReference[0] = Number.NaN;
  assert.equal(validateHash1536Readiness(invalidReference), false);

  const changedReference = validReadiness();
  changedReference.geometryReference[0] = 0;
  assert.equal(validateHash1536Readiness(changedReference), false);
});

test("rejects any attempt to mark unresolved qualification as authorized", () => {
  const contract = validReadiness();
  contract.qualification.authorized = true;
  assert.equal(validateHash1536Readiness(contract), false);
});

test("rejects altered launch identity, event label, or gate", () => {
  for (const [field, value] of [
    ["kind", "POST_LAUNCH_EXTENSION"],
    ["eventName", "sha1536"],
    ["liveGate", "OPEN"],
  ]) {
    const contract = validReadiness();
    contract[field] = value;
    assert.equal(validateHash1536Readiness(contract), false);
  }
});
