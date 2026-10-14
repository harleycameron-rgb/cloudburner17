// Local synthetic diagnostics only. No lifecycle or network dependencies.
export const CHANNELS = Object.freeze([
  "TAP_CONVEX", "SURFACE_CONCAVE", "GAIN_PSYCHOSOCIAL", "HABITATAT_DOMAIN",
  "TIME_CHRONO", "SPACE_CHRONO", "SCANROOT_LINEAGE", "SCANDOCZERO_AUDIT",
]);
export const NORMALS = Object.freeze([
  [1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1],
].map(Object.freeze));
const copy = value => structuredClone(value);
export function freeze(value) {
  if (value && typeof value === "object") {
    Object.values(value).forEach(freeze);
    Object.freeze(value);
  }
  return value;
}
function requireValue(ok, message) {
  if (!ok) throw new TypeError(message);
}
const finite = value => typeof value === "number" && Number.isFinite(value);
const vector = value => Array.isArray(value) && value.length === 3 && value.every(finite);
const norm = value => Math.hypot(...value);
const sub = (a, b) => a.map((v, i) => v - b[i]);
const distance = (a, b) => norm(sub(a, b));
const dot = (a, b) => a.reduce((s, v, i) => s + v * b[i], 0);
export function canonical(value) {
  if (value === null || typeof value === "boolean" || typeof value === "string") return JSON.stringify(value);
  if (finite(value)) return JSON.stringify(value);
  if (Array.isArray(value)) return `[${Array.from(value, canonical).join(",")}]`;
  requireValue(value && Object.getPrototypeOf(value) === Object.prototype, "Non-JSON value");
  return `{${Object.keys(value).sort().map(k => `${JSON.stringify(k)}:${canonical(value[k])}`).join(",")}}`;
}
export async function digest(value) {
  const crypto = globalThis.crypto ?? (await import("node:crypto")).webcrypto;
  const bytes = await crypto.subtle.digest("SHA-512", new TextEncoder().encode(canonical(value)));
  return Array.from(new Uint8Array(bytes), b => b.toString(16).padStart(2, "0")).join("");
}
export const MODEL = freeze({
  schema: "scandoc-synthetic/1", adapter: "tentacled-sphere-names/1",
  provenance: { kind: "synthetic", measured: false, source: "src/tentacled_sphere.py",
    sourceCommit: "ed9e5d68a9500eb506a5deba87adab9343f6505a",
    originHash: null, burnReceipt: null, sourceCommitIsBurnReceipt: false },
  frame: { name: "native-sphere-cartesian", origin: [1024, 1024, 0],
    units: { length: "diagnostic-unit", time: "synthetic-second", angle: "radian" } },
  baseline: { C: [1024, 1024, 0], ell0: 1, Q: [[1, 0, 0], [0, 1, 0], [0, 0, 1]] },
  frequency: { schema: "synthetic-phase/1", value: 0.25, units: "cycles/synthetic-second",
    phase0: 0, epoch: 0, law: "phase0 + 2*pi*value*(time-epoch)", physical: false },
  evolution: { schema: "linear-demo/1", step: 1, ticks: 5,
    initialCenterOffset: [2, 0, 0], velocity: [-0.1, 0, 0], initialRadius: 1,
    radiusRate: -0.05, faceContractionRate: 0.05 },
  policies: { schema: "v0.6-local/1", epsilon: 1e-9, closureDistance: 2,
    endpointTolerance: 0.01, segment: "disabled", transitions: "forbidden" },
  channels: CHANNELS.map(name => ({ name, status: "unresolved", face: null, evidence: null })),
  metadata: { cmbInspired: { scoreConstant: 0.1137, physicalCalibration: false } },
  rendering: { spiralBack: "visual-only", pyramidNose: "visual-only", torsionRule: null },
});
export function baseline(config) {
  const { C, ell0, Q } = config;
  requireValue(vector(C) && finite(ell0) && ell0 > 0 &&
    Array.isArray(Q) && Q.length === 3 && Q.every(vector), "Invalid baseline");
  const det = Q[0][0]*(Q[1][1]*Q[2][2]-Q[1][2]*Q[2][1]) -
    Q[0][1]*(Q[1][0]*Q[2][2]-Q[1][2]*Q[2][0]) +
    Q[0][2]*(Q[1][0]*Q[2][1]-Q[1][1]*Q[2][0]);
  requireValue(Math.abs(det - 1) < 1e-9 && Q.every((row, i) =>
    Q.every((other, j) => Math.abs(dot(row, other) - Number(i === j)) < 1e-9)), "Q must be proper orthonormal");
  const anchors = NORMALS.map(n => C.map((c, i) => c + ell0 * dot(Q[i], n)));
  requireValue(anchors.every(vector), "Non-finite baseline anchors");
  return anchors;
}
function validateFrame(frame) {
  requireValue(frame && vector(frame.origin) && typeof frame.name === "string" &&
    frame.name.length > 0 && frame.units && ["length", "time", "angle"].every(k =>
      typeof frame.units[k] === "string" && frame.units[k].length > 0), "Invalid frame/units");
}
function validateState(state, model) {
  requireValue(state && Number.isSafeInteger(state.tick) && state.tick >= 0 &&
    finite(state.time), "Invalid tick/time");
  requireValue(canonical(state.frame) === canonical(model.frame), "Inconsistent frame/units");
  requireValue(Array.isArray(state.faces) && state.faces.length === 6 &&
    state.faces.every((f, i) => f.id === ["+X", "-X", "+Y", "-Y", "+Z", "-Z"][i] &&
      vector(f.position) && canonical(f.anchor) === canonical(baseline(model.baseline)[i])),
  "Six ordered faces and fixed anchors required");
  requireValue(state.sphere && vector(state.sphere.center) && finite(state.sphere.radius) &&
    state.sphere.radius > 0 && vector(state.sphere.velocity) && vector(state.sentinel),
  "Invalid Sphere or Sentinel");
  requireValue(canonical(state.sentinel) === canonical(model.frame.origin), "Fixed Sentinel required");
}
export function medianCore(state, config) {
  const anchors = baseline(config);
  requireValue(state.faces?.length === 6 && state.faces.every(f => vector(f.position)), "Six finite faces required");
  // Individual residual vectors never leave this verifier.
  const legs = state.faces.map((f, i) => distance(f.position, anchors[i]) / config.ell0).sort((a, b) => a - b);
  requireValue(legs.every(finite), "Non-finite normalized legs");
  return legs[2] / 2 + legs[3] / 2;
}
export function validateTrajectory(states, model = MODEL) {
  canonical(states);
  validateFrame(model.frame);
  baseline(model.baseline);
  requireValue(canonical(model.frame.origin) === canonical(model.baseline.C), "Shared origin required");
  requireValue(states.length > 0, "Empty trajectory");
  states.forEach((state, i) => {
    validateState(state, model);
    if (i) {
      const prev = states[i - 1], dt = state.time - prev.time;
      requireValue(state.tick > prev.tick && finite(dt) && dt > 0, "Time/ticks must increase");
      requireValue(state.sphere.velocity.every((v, k) =>
        Math.abs(v - (state.sphere.center[k] - prev.sphere.center[k]) / dt) < 1e-9), "Velocity mismatch");
    }
  });
  return true;
}
export function verifyBoundary(states, evidence, model = MODEL) {
  validateTrajectory(states, model);
  const p = model.policies;
  requireValue(finite(p.epsilon) && p.epsilon > 0 && finite(p.closureDistance) &&
    p.closureDistance >= 0 && finite(p.endpointTolerance) && p.endpointTolerance >= 0 &&
    ["disabled", "linear"].includes(p.segment), "Invalid policy");
  const unresolved = ["read-only context cannot authenticate measured evidence"], failed = [];
  const last = states.at(-1), prev = states.at(-2);
  if (!evidence || evidence.kind !== "measured" || !evidence.receipt || !evidence.originHash)
    unresolved.push("trusted measured evidence/origin/receipt missing");
  if (!evidence || !finite(evidence.six) || !finite(evidence.seven) ||
      Math.abs(evidence.six) <= p.epsilon || Math.abs(evidence.seven) <= p.epsilon)
    unresolved.push("six/seven denominator unresolved");
  if (!evidence || ![evidence.residue, evidence.inner, evidence.outer].every(finite))
    unresolved.push("nested containment missing");
  else if (!(0 <= evidence.residue && evidence.residue <= evidence.inner && evidence.inner <= evidence.outer))
    failed.push("nested containment");
  if (Math.max(...last.faces.map(f => distance(f.position, last.sphere.center))) > p.closureDistance)
    failed.push("max-distance closure");
  const meanRadius = s => s.faces.reduce((sum, f) => sum + distance(f.position, s.sphere.center), 0) / 6;
  if (!prev) unresolved.push("closure rate missing");
  else if ((meanRadius(prev) - meanRadius(last)) / (last.time - prev.time) <= p.epsilon)
    failed.push("positive inward mean-radius closure rate");
  if (!evidence || !vector(evidence.endpoint)) unresolved.push("actual endpoint missing");
  else if (distance(last.sphere.center, evidence.endpoint) > p.endpointTolerance) failed.push("actual endpoint proximity");
  let segmentIntersection = null;
  if (p.segment === "linear") {
    if (!prev || !evidence || !vector(evidence.endpoint)) unresolved.push("linear segment evidence missing");
    else {
      const d = sub(last.sphere.center, prev.sphere.center), length2 = dot(d, d);
      const t = length2 === 0 ? 0 : Math.max(0, Math.min(1, dot(sub(evidence.endpoint, prev.sphere.center), d) / length2));
      segmentIntersection = distance(prev.sphere.center.map((v, i) => v + t*d[i]), evidence.endpoint) <= p.endpointTolerance;
    }
  }
  return freeze({ status: failed.length ? "rejected" : "unresolved", failed, unresolved,
    segmentIntersection, transitionAuthorized: false, structuralMeltingAttachment: false });
}
export function adaptSourceChannels(source) {
  requireValue(source && CHANNELS.every(k => Object.hasOwn(source, k)) &&
    Object.keys(source).length === 8, "Exactly eight named source channels required");
  canonical(source);
  return freeze({ schema: MODEL.adapter, channels: CHANNELS.map(name => ({
    name, source: copy(source[name]), face: null, status: "supplied-unverified",
  })), mapping: "six-faces-independent-of-eight-channels", sharedOrigin: copy(MODEL.frame.origin) });
}
export async function syntheticDemo(model = MODEL) {
  model = freeze(copy(model));
  canonical(model);
  requireValue(model.schema === MODEL.schema && model.provenance.kind === "synthetic" &&
    model.provenance.measured === false && model.provenance.originHash === null &&
    model.provenance.burnReceipt === null && model.rendering.torsionRule === null &&
    canonical(model.channels) === canonical(MODEL.channels), "Synthetic model labels/boundaries required");
  baseline(model.baseline);
  const e = model.evolution, f = model.frequency;
  requireValue(Number.isSafeInteger(e.ticks) && e.ticks >= 2 && e.ticks <= 256 &&
    finite(e.step) && e.step > 0 && vector(e.initialCenterOffset) && vector(e.velocity) &&
    [e.initialRadius, e.radiusRate, e.faceContractionRate, f.value, f.phase0, f.epoch].every(finite) &&
    f.value > 0 && f.schema === "synthetic-phase/1" &&
    f.units === `cycles/${model.frame.units.time}` && f.law === MODEL.frequency.law && f.physical === false,
  "Invalid synthetic evolution/frequency");
  const anchors = baseline(model.baseline);
  const trajectory = Array.from({ length: e.ticks }, (_, tick) => {
    const time = tick * e.step, scale = 1 - e.faceContractionRate*time;
    requireValue(scale > 0, "Positive face scale required");
    return { tick, time, frame: copy(model.frame),
      faces: anchors.map((anchor, i) => ({ id: ["+X", "-X", "+Y", "-Y", "+Z", "-Z"][i],
        anchor, position: model.baseline.C.map((v, k) => v + scale*(anchor[k]-v)) })),
      sphere: { center: model.frame.origin.map((v, i) => v + e.initialCenterOffset[i] + e.velocity[i]*time),
        radius: e.initialRadius + e.radiusRate*time, velocity: copy(e.velocity) },
      sentinel: copy(model.frame.origin) };
  });
  validateTrajectory(trajectory, model);
  const last = trajectory.at(-1);
  const halfExtent = model.baseline.ell0 * (1 - e.faceContractionRate*last.time);
  const vertices = [-1, 1].flatMap(x => [-1, 1].flatMap(y => [-1, 1].map(z =>
    model.baseline.C.map((c, i) => c + halfExtent*dot(model.baseline.Q[i], [x, y, z])))));
  const cubeState = { schema: "complete-cube/1", model: copy(model), state: copy(last),
    geometry: { center: copy(model.baseline.C), orientation: copy(model.baseline.Q),
      halfExtent, vertices, faceVertices: [[4, 5, 7, 6], [0, 2, 3, 1],
        [2, 6, 7, 3], [0, 1, 5, 4], [1, 3, 7, 5], [0, 4, 6, 2]] } };
  const modelDigest = await digest(model), cubeDigest = await digest(cubeState);
  const perFaceDigests = await Promise.all(cubeState.state.faces.map(face => digest({
    modelDigest, frame: model.frame, tick: cubeState.state.tick, time: cubeState.state.time, face,
  })));
  const trajectoryDigest = await digest(trajectory);
  const phase = f.phase0 + 2*Math.PI*f.value*(last.time-f.epoch);
  requireValue(finite(phase), "Non-finite synthetic phase");
  return freeze({ schema: "scandoc-demo-export/1", synthetic: true, model: copy(model),
    modelDigest, cubeState, cubeDigest, perFaceDigests, trajectory, trajectoryDigest,
    frequency: copy(f), phase,
    median: medianCore(trajectory.at(-1), model.baseline),
    sentinelSeparation: distance(trajectory.at(-1).sphere.center, trajectory.at(-1).sentinel),
    boundary: verifyBoundary(trajectory, null, model), genesisReceipt: null,
    transmission: "disabled", physicalConvergence: false });
}
function seedBody(demo) {
  const last = demo.trajectory.at(-1);
  return freeze({
    schema: "scandoc-context/1", synthetic: true, transmission: "disabled",
    frame: copy(demo.model.frame), sentinel: copy(last.sentinel),
    cubeCommitment: demo.cubeDigest, modelDigest: demo.modelDigest,
    channels: CHANNELS.map(name => ({ name, face: null, status: "unresolved" })),
    median: medianCore(last, demo.model.baseline),
    radiusPrefix: demo.trajectory.map(s => ({ tick: s.tick, time: s.time, radius: s.sphere.radius,
      center: copy(s.sphere.center), velocity: copy(s.sphere.velocity) })),
    trajectoryDigest: demo.trajectoryDigest, baseline: copy(demo.model.baseline),
    policies: copy(demo.model.policies), frequency: copy(demo.model.frequency),
    originHash: demo.model.provenance.originHash,
  });
}
export async function createController(demo, trustedCheckpoint) {
  demo = freeze(copy(demo));
  trustedCheckpoint = freeze(copy(trustedCheckpoint));
  requireValue(demo.synthetic === true && await digest(demo.model) === demo.modelDigest &&
    await digest(demo.cubeState) === demo.cubeDigest &&
    await digest(demo.trajectory) === demo.trajectoryDigest, "Invalid demo commitments");
  validateTrajectory(demo.trajectory, demo.model);
  requireValue(canonical(demo.cubeState.state) === canonical(demo.trajectory.at(-1)) &&
    canonical(demo.cubeState.model) === canonical(demo.model), "Cube/prefix mismatch");
  const observed = freeze(copy(demo.trajectory));
  const body = seedBody(demo);
  const seedHash = await digest(body);
  requireValue(trustedCheckpoint?.kind === "local-synthetic-checkpoint" &&
    trustedCheckpoint.seedHash === seedHash && trustedCheckpoint.cubeDigest === demo.cubeDigest &&
    trustedCheckpoint.trajectoryDigest === demo.trajectoryDigest, "Trusted checkpoint mismatch");
  let forecasts = freeze([]);
  return Object.freeze({
    observed, body, seedHash,
    requestContext: () => freeze({ body, seedHash, originStatus: body.originHash ? "supplied-unverified" : "unresolved",
      receiptStatus: "unresolved", authority: "read-only", transmission: "disabled" }),
    suppliedFiringResult: async supplied => {
      supplied = copy(supplied);
      requireValue(supplied && canonical(supplied.body) === canonical(body) &&
        await digest(supplied.body) === seedHash, "Full canonical seed mismatch");
      requireValue(Array.isArray(supplied.proposals) && supplied.proposals.length > 0, "Missing proposals");
      const next = copy(supplied.proposals);
      requireValue(next.length <= 256, "Too many forecast ticks");
      const start = observed.at(-1);
      requireValue(next.every((s, i) => s.tick === start.tick + i + 1), "Next ticks only");
      validateTrajectory([...observed, ...next], demo.model);
      forecasts = freeze(next);
      return freeze({ stream: "forecast", status: "unverified-proposal", states: forecasts,
        observedDigest: demo.trajectoryDigest, transitionAuthorized: false });
    },
    forecast: () => forecasts,
  });
}
export async function contextSeed(demo) {
  // Bootstrap a local checkpoint, not a genesis/burn receipt or authentication.
  const body = seedBody(demo);
  return freeze({ kind: "local-synthetic-checkpoint", seedHash: await digest(body),
    cubeDigest: demo.cubeDigest, trajectoryDigest: demo.trajectoryDigest });
}
export function toCSV(demo) {
  const header = ["synthetic", "tick", "time", "x", "y", "z", "radius", "vx", "vy", "vz",
    "sentinelSeparation", "median", "frequency", "frequencyUnits", "lengthUnits", "timeUnits",
    "cubeDigest", "perFaceDigests", "trajectoryDigest", "provenance"];
  const quote = v => `"${String(v).replaceAll('"', '""')}"`;
  return [header, ...demo.trajectory.map(s => [true, s.tick, s.time, ...s.sphere.center,
    s.sphere.radius, ...s.sphere.velocity, distance(s.sphere.center, s.sentinel),
    medianCore(s, demo.model.baseline), demo.frequency.value, demo.frequency.units,
    s.frame.units.length, s.frame.units.time, demo.cubeDigest, demo.perFaceDigests.join(";"),
    demo.trajectoryDigest, canonical(demo.model.provenance)])].map(row => row.map(quote).join(",")).join("\n") + "\n";
}
