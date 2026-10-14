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
function requireValue(ok, message, code = "INVALID_INPUT") {
  if (!ok) {
    const error = new TypeError(message);
    error.code = code;
    throw error;
  }
}
const finite = value => typeof value === "number" && Number.isFinite(value);
const vector = value => Array.isArray(value) && value.length === 3 && Array.from(value).every(finite);
function checked(value) {
  requireValue(finite(value), "Non-finite derived calculation");
  return value;
}
const norm = value => checked(Math.hypot(...value));
const sub = (a, b) => a.map((v, i) => checked(v - b[i]));
const distance = (a, b) => norm(sub(a, b));
const dot = (a, b) => a.reduce((s, v, i) => checked(s + checked(v * b[i])), 0);
function keys(value, required, optional = []) {
  requireValue(value && Object.getPrototypeOf(value) === Object.prototype &&
    required.every(k => Object.hasOwn(value, k)) &&
    Object.keys(value).every(k => required.includes(k) || optional.includes(k)),
  `Exact schema required: ${required.join(",")}`);
}
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
  schema: "scandoc-synthetic/2", adapter: "tentacled-sphere-names/1",
  provenance: { kind: "synthetic", measured: false, source: "src/tentacled_sphere.py",
    sourceCommit: "ed9e5d68a9500eb506a5deba87adab9343f6505a",
    originHash: null, originStatus: "UNRESOLVED_NO_ORIGIN_RECEIPT",
    burnReceipt: null, sourceCommitIsBurnReceipt: false },
  frame: { name: "native-sphere-cartesian", origin: [1024, 1024, 0],
    units: { length: "diagnostic-unit", time: "synthetic-second", angle: "radian" } },
  baseline: { C: [1024, 1024, 0], ell0: 1, Q: [[1, 0, 0], [0, 1, 0], [0, 0, 1]] },
  frequency: { schema: "synthetic-phase/1", value: 0.25, units: "cycles/synthetic-second",
    phase0: 0, epoch: 0, law: "phase0 + 2*pi*value*(time-epoch)", physical: false },
  evolution: { schema: "linear-demo/1", step: 1, ticks: 5,
    initialCenterOffset: [2, 0, 0], velocity: [-0.1, 0, 0], initialRadius: 1,
    radiusRate: -0.05, faceContractionRate: 0.05 },
  policies: { schema: "v0.6-local/2", epsilon: 1e-9, rateTolerance: 1e-9, closureDistance: 2,
    endpointTolerance: 0.01, segment: "disabled", transitions: "forbidden" },
  forecastPolicy: { schema: "linear-next/1", source: "linear-demo/1",
    time: "tick*step", radius: "initialRadius+radiusRate*time",
    center: "origin+initialCenterOffset+velocity*time",
    faces: "C+(1-faceContractionRate*time)*(anchor-C)", maxTicks: 256 },
  channels: CHANNELS.map(name => ({ name, status: "unresolved", face: null, evidence: null })),
  metadata: { cmb: { temperature: { value: null, units: "K", status: "UNRESOLVED" },
    anisotropy: { value: null, units: "dimensionless", status: "UNRESOLVED" },
    physicalCalibration: false },
  arbitraryScore: { value: 0.1137, units: "custom-score", physicalCalibration: false },
  mappings: { baselineCalibration: "synthetic-only", sourceChannels: "incomplete-unresolved" } },
  rendering: { spiralBack: "visual-only", pyramidNose: "visual-only", torsionRule: null },
});
export function baseline(config) {
  keys(config, ["C", "ell0", "Q"]);
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
  keys(frame, ["name", "origin", "units"]);
  keys(frame.units, ["length", "time", "angle"]);
  requireValue(frame && vector(frame.origin) && typeof frame.name === "string" &&
    frame.name.length > 0 && frame.units && ["length", "time", "angle"].every(k =>
      typeof frame.units[k] === "string" && frame.units[k].length > 0), "Invalid frame/units");
}
function validateModel(model) {
  canonical(model);
  keys(model, Object.keys(MODEL));
  for (const section of ["provenance", "baseline", "frequency", "evolution", "policies", "rendering"])
    keys(model[section], Object.keys(MODEL[section]));
  validateFrame(model.frame);
  baseline(model.baseline);
  requireValue(canonical(model.frame.origin) === canonical(model.baseline.C), "Shared origin required");
  const p = model.policies, e = model.evolution, f = model.frequency;
  requireValue(p.schema === MODEL.policies.schema && finite(p.epsilon) && p.epsilon > 0 &&
    finite(p.rateTolerance) && p.rateTolerance > 0 &&
    finite(p.closureDistance) && p.closureDistance >= 0 &&
    finite(p.endpointTolerance) && p.endpointTolerance >= 0 &&
    ["disabled", "linear"].includes(p.segment) && p.transitions === "forbidden", "Invalid policy");
  requireValue(model.schema === MODEL.schema && model.adapter === MODEL.adapter &&
    model.provenance.kind === "synthetic" && model.provenance.measured === false &&
    model.provenance.originHash === null && model.provenance.burnReceipt === null &&
    model.provenance.originStatus === MODEL.provenance.originStatus &&
    model.provenance.sourceCommitIsBurnReceipt === false &&
    canonical(model.channels) === canonical(MODEL.channels) &&
    canonical(model.metadata) === canonical(MODEL.metadata) &&
    canonical(model.rendering) === canonical(MODEL.rendering) &&
    canonical(model.forecastPolicy) === canonical(MODEL.forecastPolicy),
  "Synthetic labels, mappings and versioned rules required");
  requireValue(e.schema === "linear-demo/1" &&
    Number.isSafeInteger(e.ticks) && e.ticks >= 2 && e.ticks <= 256 &&
    finite(e.step) && e.step > 0 && vector(e.initialCenterOffset) && vector(e.velocity) &&
    [e.initialRadius, e.radiusRate, e.faceContractionRate, f.value, f.phase0, f.epoch].every(finite) &&
    e.initialRadius > 0 && f.value > 0 && f.schema === "synthetic-phase/1" &&
    f.units === `cycles/${model.frame.units.time}` && f.law === MODEL.frequency.law && f.physical === false,
  "Invalid synthetic evolution/frequency");
}
function validateState(state, model) {
  keys(state, ["tick", "time", "frame", "faces", "sphere", "sentinel"]);
  requireValue(state && Number.isSafeInteger(state.tick) && state.tick >= 0 &&
    finite(state.time), "Invalid tick/time");
  requireValue(canonical(state.frame) === canonical(model.frame), "Inconsistent frame/units");
  requireValue(Array.isArray(state.faces) && state.faces.length === 6, "Six faces required");
  state.faces.forEach(f => keys(f, ["id", "anchor", "position"]));
  requireValue(Array.isArray(state.faces) && state.faces.length === 6 &&
    state.faces.every((f, i) => f.id === ["+X", "-X", "+Y", "-Y", "+Z", "-Z"][i] &&
      vector(f.position) && canonical(f.anchor) === canonical(baseline(model.baseline)[i])),
  "Six ordered faces and fixed anchors required");
  keys(state.sphere, ["center", "radius", "velocity"]);
  requireValue(vector(state.sphere.center) && finite(state.sphere.radius) &&
    state.sphere.radius > 0 && vector(state.sphere.velocity) && vector(state.sentinel),
  "Invalid Sphere or Sentinel");
  requireValue(canonical(state.sentinel) === canonical(model.frame.origin), "Fixed Sentinel required");
  state.faces.forEach(f => distance(f.position, model.baseline.C));
  distance(state.sphere.center, state.sentinel);
  medianCore(state, model.baseline);
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
  validateModel(model);
  requireValue(Array.isArray(states) && states.length > 0, "Empty trajectory");
  states.forEach((state, i) => {
    validateState(state, model);
    if (i) {
      const prev = states[i - 1], dt = state.time - prev.time;
      requireValue(state.tick > prev.tick && finite(dt) && dt > 0, "Time/ticks must increase");
      const velocity = sub(state.sphere.center, prev.sphere.center).map(v => checked(v / dt));
      requireValue(state.sphere.velocity.every((v, k) =>
        Math.abs(checked(v - velocity[k])) <= model.policies.epsilon), "Velocity mismatch");
    }
  });
  return true;
}
export function verifyBoundary(states, evidence, model = MODEL) {
  const authority = { transitionAuthorized: false, structuralMeltingAttachment: false };
  try {
    validateTrajectory(states, model);
    if (evidence !== null && evidence !== undefined) {
      canonical(evidence);
      keys(evidence, [], ["kind", "receipt", "originHash", "residue", "inner", "outer", "endpoint"]);
      for (const key of ["kind", "receipt", "originHash"])
        if (Object.hasOwn(evidence, key))
          requireValue(typeof evidence[key] === "string" && evidence[key].length > 0 &&
            (key !== "kind" || evidence[key] === "measured"), "Malformed evidence label");
      for (const key of ["residue", "inner", "outer"])
        if (Object.hasOwn(evidence, key))
          requireValue(finite(evidence[key]) && evidence[key] >= 0, "Invalid containment bounds");
      if (Object.hasOwn(evidence, "endpoint")) requireValue(vector(evidence.endpoint), "Malformed endpoint");
    }
    const p = model.policies, last = states.at(-1), prev = states.at(-2);
    const radii = s => s.faces.map(f => distance(f.position, model.baseline.C));
    const mean = s => radii(s).reduce((sum, r) => checked(sum + r / 6), 0);
    const maximum = Math.max(...radii(last));
    const dt = prev ? checked(last.time - prev.time) : null;
    const c6 = prev ? checked(checked(mean(prev) - mean(last)) / dt) : null;
    const v7 = prev ? checked(checked(distance(last.sentinel, last.sphere.center) -
      distance(prev.sentinel, prev.sphere.center)) / dt) : null;
    const ratioResolved = v7 !== null && Math.abs(v7) > p.rateTolerance;
    const ratio = { schema: "sampled-c6-v7/1", c6, v7,
      rateUnits: `${model.frame.units.length}/${model.frame.units.time}`,
      value: ratioResolved ? checked(c6 / Math.abs(v7)) : null,
      status: ratioResolved ? "RESOLVED_SYNTHETIC" : "UNRESOLVED" };
    const closure = maximum <= p.closureDistance ? "CLOSED" : "NOT_CLOSED";
    const motion = c6 === null ? "UNRESOLVED" : c6 > p.rateTolerance ? "CLOSING" :
      c6 < -p.rateTolerance ? "EXPANDING" : "STATIONARY";
    const containment = ["residue", "inner", "outer"].every(k => finite(evidence?.[k])) ?
      (evidence.residue <= evidence.inner && evidence.inner <= evidence.outer ? "CONTAINED" : "CONTAINMENT_BREACH") : "UNRESOLVED";
    const endpoint = evidence?.endpoint ? (distance(last.sphere.center, evidence.endpoint) <=
      p.endpointTolerance ? "PROXIMATE" : "ENDPOINT_MISMATCH") : "UNRESOLVED";
    let segmentIntersection = null;
    if (p.segment === "linear" && prev && evidence?.endpoint) {
      const d = sub(last.sphere.center, prev.sphere.center), length2 = dot(d, d);
      const t = length2 === 0 ? 0 : Math.max(0, Math.min(1,
        checked(dot(sub(evidence.endpoint, prev.sphere.center), d) / length2)));
      segmentIntersection = distance(prev.sphere.center.map((v, i) => checked(v + checked(t*d[i]))),
        evidence.endpoint) <= p.endpointTolerance;
    }
    const unresolved = ["read-only context cannot authenticate measured evidence", "torsion rule missing"];
    if (!evidence?.receipt || !evidence?.originHash) unresolved.push("trusted measured evidence/origin/receipt missing");
    if (!ratioResolved) unresolved.push("c6/abs(v7) denominator or previous sample unresolved");
    if (containment === "UNRESOLVED") unresolved.push("nested containment missing");
    if (endpoint === "UNRESOLVED") unresolved.push("actual endpoint missing");
    return freeze({ status: containment === "CONTAINMENT_BREACH" ? containment :
      endpoint === "ENDPOINT_MISMATCH" ? endpoint : "UNRESOLVED",
    geometryAcceptance: "ACCEPTED", physicalEvidence: "UNRESOLVED",
    closure, motion, referenceCenter: copy(model.baseline.C), maximumDistance: maximum,
    meanDistance: mean(last), ratio, containment, endpoint, torsion: "UNRESOLVED",
    unresolved, segmentIntersection, ...authority });
  } catch (error) {
    return freeze({ status: "INVALID_INPUT", geometryAcceptance: "INVALID_INPUT",
      physicalEvidence: "UNRESOLVED", error: error.message, ...authority });
  }
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
  validateModel(model);
  const e = model.evolution, f = model.frequency;
  const trajectory = Array.from({ length: e.ticks }, (_, tick) => linearState(model, tick));
  validateTrajectory(trajectory, model);
  const last = trajectory.at(-1);
  const halfExtent = checked(model.baseline.ell0 * checked(1 - checked(e.faceContractionRate*last.time)));
  const vertices = [-1, 1].flatMap(x => [-1, 1].flatMap(y => [-1, 1].map(z =>
    model.baseline.C.map((c, i) => checked(c + checked(halfExtent*dot(model.baseline.Q[i], [x, y, z])))))));
  const cubeState = { schema: "complete-cube/2", model: copy(model), state: copy(last),
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
  const boundary = verifyBoundary(trajectory, null, model);
  requireValue(boundary.status !== "INVALID_INPUT", boundary.error);
  return freeze({ schema: "scandoc-demo-export/2", synthetic: true, model: copy(model),
    modelDigest, cubeState, cubeDigest, perFaceDigests, trajectory, trajectoryDigest,
    frequency: copy(f), phase,
    median: medianCore(trajectory.at(-1), model.baseline),
    sentinelSeparation: distance(trajectory.at(-1).sphere.center, trajectory.at(-1).sentinel),
    centerDistanceFromRadiusOrigin: distance(last.sphere.center, model.frame.origin),
    originStatus: model.provenance.originStatus,
    boundary, genesisReceipt: null,
    transmission: "disabled", physicalConvergence: false });
}
function seedBody(demo) {
  const last = demo.trajectory.at(-1);
  return freeze({
    schema: "scandoc-context/2", synthetic: true, transmission: "disabled",
    frame: copy(demo.model.frame), sentinel: copy(last.sentinel),
    cubeCommitment: demo.cubeDigest, modelDigest: demo.modelDigest,
    channels: CHANNELS.map(name => ({ name, face: null, status: "unresolved" })),
    median: medianCore(last, demo.model.baseline),
    radiusPrefix: demo.trajectory.map(s => ({ tick: s.tick, time: s.time, radius: s.sphere.radius,
      centerDistanceFromRadiusOrigin: distance(s.sphere.center, demo.model.frame.origin),
      center: copy(s.sphere.center), velocity: copy(s.sphere.velocity) })),
    trajectoryDigest: demo.trajectoryDigest, baseline: copy(demo.model.baseline),
    policies: copy(demo.model.policies), frequency: copy(demo.model.frequency),
    evolution: copy(demo.model.evolution), forecastPolicy: copy(demo.model.forecastPolicy),
    originHash: demo.model.provenance.originHash,
    originStatus: demo.model.provenance.originStatus, torsionStatus: "UNRESOLVED",
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
  const reproduced = await syntheticDemo(demo.model);
  requireValue(canonical(demo) === canonical(reproduced), "Demo must reproduce committed synthetic source");
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
      keys(supplied, ["body", "proposals"]);
      requireValue(supplied && canonical(supplied.body) === canonical(body) &&
        await digest(supplied.body) === seedHash, "Full canonical seed mismatch");
      requireValue(Array.isArray(supplied.proposals) && supplied.proposals.length > 0, "Missing proposals");
      const next = copy(supplied.proposals);
      requireValue(next.length <= demo.model.forecastPolicy.maxTicks, "Too many forecast ticks");
      const start = observed.at(-1);
      requireValue(next.every((s, i) => s.tick === start.tick + i + 1), "Next ticks only");
      validateTrajectory([...observed, ...next], demo.model);
      for (const state of next) {
        const expected = linearState(demo.model, state.tick);
        const epsilon = demo.model.policies.epsilon;
        const close = (a, b) => Math.abs(checked(a - b)) <= epsilon;
        requireValue(state.time === expected.time &&
          close(state.sphere.radius, expected.sphere.radius) &&
          state.sphere.center.every((v, k) => close(v, expected.sphere.center[k])) &&
          state.sphere.velocity.every((v, k) => close(v, expected.sphere.velocity[k])) &&
          state.faces.every((face, i) => face.position.every((v, k) => close(v, expected.faces[i].position[k]))),
        "Forecast violates committed linear-next/1 source policy", "POLICY_REJECTION");
      }
      const boundary = verifyBoundary([...observed, ...next], null, demo.model);
      requireValue(boundary.status !== "INVALID_INPUT", boundary.error);
      const result = freeze({ stream: "forecast", status: "unverified-proposal",
        geometryAcceptance: "ACCEPTED", policyStatus: "ACCEPTED", physicalEvidence: "UNRESOLVED",
        states: next, observedDigest: demo.trajectoryDigest, boundary,
        transitionAuthorized: false });
      forecasts = result.states;
      return result;
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
function linearState(model, tick) {
  requireValue(Number.isSafeInteger(tick) && tick >= 0, "Invalid linear tick");
  const e = model.evolution, time = checked(tick * e.step);
  const scale = checked(1 - checked(e.faceContractionRate*time));
  const radius = checked(e.initialRadius + checked(e.radiusRate*time));
  requireValue(scale > 0 && radius > 0, "Linear source exhausted positive scale/radius", "POLICY_REJECTION");
  return { tick, time, frame: copy(model.frame),
    faces: baseline(model.baseline).map((anchor, i) => ({
      id: ["+X", "-X", "+Y", "-Y", "+Z", "-Z"][i], anchor,
      position: model.baseline.C.map((v, k) => checked(v + checked(scale*checked(anchor[k]-v)))),
    })),
    sphere: { center: model.frame.origin.map((v, i) =>
      checked(checked(v + e.initialCenterOffset[i]) + checked(e.velocity[i]*time))),
    radius, velocity: copy(e.velocity) }, sentinel: copy(model.frame.origin) };
}
export function nextProposal(body) {
  canonical(body);
  keys(body, Object.keys(seedBody({
    model: MODEL, trajectory: [linearState(MODEL, 0)], cubeDigest: "", modelDigest: "", trajectoryDigest: "",
  })));
  const model = { ...copy(MODEL), frame: copy(body.frame), baseline: copy(body.baseline),
    policies: copy(body.policies), evolution: copy(body.evolution), frequency: copy(body.frequency),
    forecastPolicy: copy(body.forecastPolicy) };
  validateModel(model);
  requireValue(Array.isArray(body.radiusPrefix) && body.radiusPrefix.length > 0, "Missing observed prefix");
  const tick = body.radiusPrefix.at(-1).tick + 1;
  return freeze({ body: copy(body), proposals: [linearState(model, tick)] });
}
export function toCSV(demo) {
  const header = ["synthetic", "tick", "time", "x", "y", "z", "geometricRadius", "centerDistanceFromRadiusOrigin", "vx", "vy", "vz",
    "sentinelSeparation", "median", "frequency", "frequencyUnits", "lengthUnits", "timeUnits",
    "cubeDigest", "perFaceDigests", "trajectoryDigest", "originStatus", "provenance"];
  const quote = v => `"${String(v).replaceAll('"', '""')}"`;
  return [header, ...demo.trajectory.map(s => [true, s.tick, s.time, ...s.sphere.center,
    s.sphere.radius, distance(s.sphere.center, demo.model.frame.origin), ...s.sphere.velocity, distance(s.sphere.center, s.sentinel),
    medianCore(s, demo.model.baseline), demo.frequency.value, demo.frequency.units,
    s.frame.units.length, s.frame.units.time, demo.cubeDigest, demo.perFaceDigests.join(";"),
    demo.trajectoryDigest, demo.originStatus, canonical(demo.model.provenance)])].map(row => row.map(quote).join(",")).join("\n") + "\n";
}
