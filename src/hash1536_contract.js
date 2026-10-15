export const LAUNCH_ROLES = Object.freeze([
  "TAP",
  "SURFACE",
  "GAIN",
  "HABITAT",
  "ENGINE",
  "BUSINESS",
]);

const GEOMETRY_REFERENCE = [1024, 1024, 0];

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function hasExactKeys(value, keys) {
  return isRecord(value)
    && Object.keys(value).length === keys.length
    && keys.every((key) => Object.hasOwn(value, key));
}

export function validateHash1536Readiness(value) {
  if (!hasExactKeys(value, [
    "kind",
    "eventName",
    "phase",
    "liveGate",
    "geometryReference",
    "roles",
    "qualification",
  ])) return false;

  if (value.kind !== "COORDINATED_SIX_LEG_LAUNCH"
    || value.eventName !== "hash1536"
    || value.phase !== "READINESS_ONLY"
    || value.liveGate !== "CLOSED") return false;

  if (!Array.isArray(value.geometryReference)
    || value.geometryReference.length !== GEOMETRY_REFERENCE.length
    || !GEOMETRY_REFERENCE.every((expected, index) =>
      Object.hasOwn(value.geometryReference, index)
      && Number.isFinite(value.geometryReference[index])
      && value.geometryReference[index] === expected)) {
    return false;
  }

  if (!Array.isArray(value.roles) || value.roles.length !== LAUNCH_ROLES.length) {
    return false;
  }

  const seenRoles = new Set();
  for (const roleEntry of value.roles) {
    if (!hasExactKeys(roleEntry, ["role", "logicalTick", "measurement"])
      || !LAUNCH_ROLES.includes(roleEntry.role)
      || seenRoles.has(roleEntry.role)
      || !Number.isSafeInteger(roleEntry.logicalTick)
      || roleEntry.logicalTick < 0
      || !(roleEntry.measurement === null
        || (typeof roleEntry.measurement === "number"
          && Number.isFinite(roleEntry.measurement)))) return false;
    seenRoles.add(roleEntry.role);
  }

  return seenRoles.size === LAUNCH_ROLES.length
    && hasExactKeys(value.qualification, ["status", "authorized"])
    && value.qualification.status === "UNRESOLVED"
    && value.qualification.authorized === false;
}
