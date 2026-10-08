import { createHash } from "node:crypto";

/**
 * @typedef {{curvature: number, potential: number, tension: number}} Pixel
 * @typedef {{hash: string, synthetic: boolean, qTrajectory: {q: number, timestamp: number, washburn: boolean}}} TopologyHash
 */

export const TopologyHash = Object.freeze({
  fields: Object.freeze(["hash", "synthetic", "qTrajectory"]),
});

const sha512 = (input) => createHash("sha512").update(input).digest("hex");

export function generateSyntheticStateHash(a, b) {
  for (const pixel of [a, b]) {
    if (
      pixel === null ||
      typeof pixel !== "object" ||
      !Number.isFinite(pixel.curvature) ||
      !Number.isFinite(pixel.potential) ||
      !Number.isFinite(pixel.tension)
    ) {
      throw new TypeError("Pixels must contain finite curvature, potential, and tension");
    }
  }

  const avgCurvature = (a.curvature + b.curvature) / 2;
  const avgPotential = (a.potential + b.potential) / 2;
  const avgTension = (a.tension + b.tension) / 2;
  const preimage = `${avgCurvature}:${avgPotential}:${avgTension}`;

  return Object.freeze({
    hash: sha512(preimage),
    synthetic: true,
    qTrajectory: Object.freeze({
      q: Math.random(),
      timestamp: Date.now(),
      washburn: true,
    }),
  });
}
