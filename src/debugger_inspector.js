/**
 * @typedef {Object} InspectorObject
 * @property {string} hash
 * @property {boolean} syntheticHash
 * @property {number | null} curvature
 * @property {number | null} potential
 * @property {number | null} tension
 * @property {number} qTrajectory
 * @property {import("./burn_lifecycle.js").ReceiptLifecycle | null} lifecycle
 */

export const InspectorObject = Object.freeze({
  fields: Object.freeze([
    "hash",
    "syntheticHash",
    "curvature",
    "potential",
    "tension",
    "qTrajectory",
    "lifecycle",
  ]),
});

export function inspectHashDetails(details, pixel = null, lifecycle = null) {
  if (details === null || typeof details !== "object") {
    throw new TypeError("Hash details must be an object");
  }
  const topology = details.topologyHash ?? details;
  const inspectedPixel = details.pixel ?? pixel;
  const inspectedLifecycle = details.lifecycle ?? lifecycle;
  if (typeof topology.hash !== "string") {
    throw new TypeError("Hash details must include a string hash");
  }

  return Object.freeze({
    hash: topology.hash,
    syntheticHash: topology.synthetic === true,
    curvature: Number.isFinite(inspectedPixel?.curvature)
      ? inspectedPixel.curvature
      : null,
    potential: Number.isFinite(inspectedPixel?.potential)
      ? inspectedPixel.potential
      : null,
    tension: Number.isFinite(inspectedPixel?.tension)
      ? inspectedPixel.tension
      : null,
    qTrajectory: Number.isFinite(topology.qTrajectory?.q)
      ? topology.qTrajectory.q
      : 0,
    lifecycle: inspectedLifecycle ?? null,
  });
}
