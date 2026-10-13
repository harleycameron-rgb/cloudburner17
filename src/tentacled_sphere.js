import { createHash } from "node:crypto";
import { runSphericalBurnHarness } from "../burn-harness-spherical.js";
import { verifySphericalEnvelope } from "./spherical_topology.js";

const commit = value => createHash("sha512")
  .update(JSON.stringify(value)).digest("hex");

/** Eight diagnostic arms attached to native spherical burn placements.
 * Geometry and receipts are local values, not identity or live qualification.
 */
export function createTentacledSphere({ sphere = {}, segments = 32, length = 2,
  turns = 1, amplitude = 0.2 } = {}) {
  if (!Number.isInteger(segments) || segments < 2 || segments > 256 ||
      !Number.isFinite(length) || length <= 0 || length > 100 ||
      !Number.isFinite(turns) || Math.abs(turns) > 16 ||
      !Number.isFinite(amplitude) || amplitude < 0 || amplitude > 10) {
    throw new TypeError("Invalid tentacle geometry");
  }
  const scenes = [{ id: "sphere-core", content: "declared sphere core", layer: 0 }];
  for (let i = 1; i <= 8; i++) scenes.push({ id: `arm-${i}`,
    content: `declared temporal anchor ${i}`, layer: 0, dependencies: ["sphere-core"] });
  const source = runSphericalBurnHarness(scenes, sphere);
  if (!verifySphericalEnvelope(source, source.head)) throw new Error("Invalid sphere envelope");
  const origin = source.sphere.origin;
  const radius = source.sphere.radius;
  const arms = source.events.slice(1).map((event, index) => {
    const d = event.placement.direction;
    const reference = Math.abs(d[2]) < 0.9 ? [0, 0, 1] : [0, 1, 0];
    const cross = (a, b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
    const raw = cross(reference, d);
    const norm = Math.hypot(...raw);
    const u = raw.map(v => v/norm);
    const v = cross(d, u);
    const points = Array.from({ length: segments + 1 }, (_, j) => {
      const t = j/segments;
      const angle = 2*Math.PI*turns*t;
      // Tangential displacement vanishes at the attachment point.
      return origin.map((o, k) => o + radius*((1+length*t)*d[k] +
        amplitude*t*(Math.cos(angle)*u[k] + Math.sin(angle)*v[k])));
    });
    const mapping = {
      status: "pending",
      repository: null,
      htmlPath: null,
      orrery: { fields: null, units: null, timeReference: null },
      orrerySourceCommitment: null,
    };
    const trace = {
      schema: "tentacled-sphere-trace/1",
      source: {
        kind: "synthetic-declared-scene",
        scene: structuredClone(scenes[index + 1]),
        topologyHash: event.topologyHash,
      },
      transformation: {
        kind: "native-radial-helical/1",
        segments, length, turns, amplitude,
        direction: [...d], tangentU: u, tangentV: v,
      },
      frame: {
        kind: "native-sphere-cartesian",
        units: "diagnostic-units",
        sphere: structuredClone(source.sphere),
        timeReference: null,
      },
    };
    const sourceCommitment = commit(trace.source);
    const attachment = [...event.placement.position];
    const geometryCommitment = commit({
      schema: "tentacled-sphere-geometry/1",
      id: event.id, mapping, trace, sourceCommitment, attachment, points,
    });
    return { id: event.id, dependency: "sphere-core", receipt: event.envelopeHash,
      attachment, points, status: "synthetic-tested", mapping, trace,
      sourceCommitment, geometryCommitment };
  });
  return { schema: "tentacled-sphere/1", mode: "local-diagnostic",
    source, arms, authentication: "backend-required", upstreamIntegration: false };
}
