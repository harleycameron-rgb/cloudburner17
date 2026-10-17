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

test("accepts finite role measurements without requiring them to be equal", () => {
  const contract = validReadiness();
  contract.roles.forEach((role, index) => {
    role.measurement = index + 0.5;
  });

  assert.equal(validateHash1536Readiness(contract), true);
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

test("rejects sparse geometry references, including inherited coordinates", () => {
  const sparseReferences = [
    new Array(3),
    [1024, , 0],
    [, 1024, 0],
    [1024, 1024, ,],
  ];

  const inheritedCoordinate = [1024, , 0];
  const localPrototype = Object.create(Array.prototype);
  localPrototype[1] = 1024;
  Object.setPrototypeOf(inheritedCoordinate, localPrototype);
  assert.equal(Object.hasOwn(inheritedCoordinate, 1), false);
  sparseReferences.push(inheritedCoordinate);

  for (const geometryReference of sparseReferences) {
    const contract = validReadiness();
    contract.geometryReference = geometryReference;
    assert.equal(validateHash1536Readiness(contract), false);
  }
});

test("rejects malformed records, missing or extra keys, altered phase, and qualification status", () => {
  for (const record of [null, undefined, "record", 1, true, [], ""]) {
    assert.equal(validateHash1536Readiness(record), false);
  }

  const missingKey = validReadiness();
  delete missingKey.phase;
  assert.equal(validateHash1536Readiness(missingKey), false);

  const extraKey = validReadiness();
  extraKey.unexpected = true;
  assert.equal(validateHash1536Readiness(extraKey), false);

  const alteredPhase = validReadiness();
  alteredPhase.phase = "LAUNCH";
  assert.equal(validateHash1536Readiness(alteredPhase), false);

  const alteredQualification = validReadiness();
  alteredQualification.qualification.status = "QUALIFIED";
  assert.equal(validateHash1536Readiness(alteredQualification), false);
});

test("rejects nonnumeric measurements except explicit null", () => {
  for (const measurement of [undefined, "1", true, {}, []]) {
    const contract = validReadiness();
    contract.roles[0].measurement = measurement;
    assert.equal(validateHash1536Readiness(contract), false);
  }

  const unresolved = validReadiness();
  unresolved.roles[0].measurement = null;
  assert.equal(validateHash1536Readiness(unresolved), true);
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
