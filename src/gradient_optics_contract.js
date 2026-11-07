// SCANDOC Gradient Optics v1 — pure, zero-I/O validation boundary.
// No firing authority, camera access, network, storage, or backend calls.
export const SCHEMA = "scandoc-gradient-optics-state/1";
export const TENTACLES = Object.freeze([
  "T1_TAP","T2_SURFACE","T3_GAIN","T4_HABITAT",
  "T5_ENGINE","T6_BUSINESS","T7_TIME","T8_FORETENTACLE"
]);
const LIMITS = Object.freeze({
  sensitivity:[0,1], knifeEdgeAngleDeg:[0,180], threshold:[0,1],
  contrast:[0,4], persistence:[0,1], intensity:[0,1]
});
const DOMAINS = Object.freeze({
  OPTICAL_MEASURED:"OPTICAL_OBSERVATION",
  COMPUTATIONAL_FILTER:"IMAGE_INTENSITY_GRADIENT",
  SYNTHETIC_GEOMETRY:"SYNTHETIC_STATE_GRADIENT"
});
const PROVENANCE = Object.freeze({
  OPTICAL_MEASURED:"MEASURED_OPTICAL",
  COMPUTATIONAL_FILTER:"COMPUTED_FROM_VIDEO",
  SYNTHETIC_GEOMETRY:"SYNTHETIC_SIMULATION"
});
const plain = v => v !== null && typeof v === "object" && !Array.isArray(v)
  && Object.getPrototypeOf(v) === Object.prototype;
const exactKeys = (value, allowed) => {
  if (!plain(value) || Object.keys(value).some(k => !allowed.includes(k))) throw new TypeError("Unknown or malformed fields");
};
export function validateParameters(p, partial=false) {
  exactKeys(p,Object.keys(LIMITS));
  if (!partial && Object.keys(p).length !== Object.keys(LIMITS).length) throw new TypeError("Missing filter parameters");
  for (const [k,v] of Object.entries(p)) {
    const [min,max]=LIMITS[k];
    if (typeof v!=="number" || !Number.isFinite(v) || v<min || v>max) throw new RangeError("Invalid "+k);
  }
  return Object.freeze({...p});
}
export function validateGradientState(state, expected) {
  exactKeys(state,["schema","moduleVersion","controlsVersion","sessionVersion","firingId","topologyCommitment","input","sharedPreset","localOverrides","nativeGate"]);
  if (state.schema!==SCHEMA || state.moduleVersion!=="scandoc-gradient-optics/1" ||
      state.controlsVersion!=="scandoc-controls/3" || state.sessionVersion!=="scandoc-session/2" ||
      state.nativeGate!=="CLOSED") throw new TypeError("Unsupported schema or gate");
  if (!plain(expected) || typeof expected.firingId!=="string" || !expected.firingId ||
      typeof expected.topologyCommitment!=="string" || !expected.topologyCommitment ||
      state.firingId!==expected.firingId || state.topologyCommitment!==expected.topologyCommitment) throw new TypeError("Firing/topology mismatch");
  exactKeys(state.input,["inputId","mode","domain","provenance","accessState"]);
  const i=state.input;
  if (typeof i.inputId!=="string" || !i.inputId || typeof i.mode!=="string" ||
      !Object.hasOwn(DOMAINS,i.mode) ||
      i.domain!==DOMAINS[i.mode] || i.provenance!==PROVENANCE[i.mode] ||
      !["MANUAL","REQUESTING","AVAILABLE","DENIED_OR_UNAVAILABLE","INTERRUPTED"].includes(i.accessState)) throw new TypeError("Invalid input provenance");
  validateParameters(state.sharedPreset);
  if (!plain(state.localOverrides)) throw new TypeError("Invalid overrides");
  for (const [id,p] of Object.entries(state.localOverrides)) {
    if (!TENTACLES.includes(id)) throw new TypeError("Unknown tentacle");
    validateParameters(p,true);
  }
  return true;
}
export function assertProjectionAllowed(tentacleId, separated) {
  if (!TENTACLES.includes(tentacleId)) throw new TypeError("Unknown tentacle");
  if (typeof separated!=="boolean") throw new TypeError("Invalid separation state");
  if (!separated && (tentacleId==="T7_TIME" || tentacleId==="T8_FORETENTACLE"))
    throw new Error("Post-separation tentacle cannot project before separation");
  return true;
}
