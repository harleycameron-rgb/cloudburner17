// SCANDOC Gradient Optics: deterministic synthetic projection, no I/O.
// Visual coordinates are derived from the supplied state; no topology mutation.
import { assertProjectionAllowed, validateParameters } from "./gradient_optics_contract.js";
const finite = n => typeof n==="number" && Number.isFinite(n);
const vec3 = v => Array.isArray(v) && v.length===3 && v.every(finite);
const norm = v => Math.hypot(...v);
const clamp = (v,a,b) => Math.max(a,Math.min(b,v));
const unit = v => { const n=norm(v); return n>1e-12?v.map(x=>x/n):[0,0,0]; };
const dot = (a,b) => a.reduce((s,v,i)=>s+v*b[i],0);
const projection = {
  T1_TAP: ([x,y,z]) => Math.hypot(x,y,z),
  T2_SURFACE: ([x,y,z]) => Math.hypot(x,y)-Math.abs(z),
  T3_GAIN: ([x]) => x,
  T4_HABITAT: ([x]) => -x,
  T5_ENGINE: ([x,y,z]) => z+Math.hypot(x,y)*0.25,
  T6_BUSINESS: ([x,y,z]) => -z-Math.hypot(x,y)*0.25,
  T7_TIME: ([x,y,z]) => Math.hypot(x,y,z),
  T8_FORETENTACLE: ([x,y,z]) => Math.abs(x)+Math.abs(y)+Math.abs(z)
};
/**
 * Operates only on synthetic vectors in the declared local origin frame.
 * Not optical schlieren measurement; not a density or refractive-index estimate.
 * For T7, previousGradient is a previously recorded vector; no interpolation.
 */
export function projectSyntheticGradient({
  tentacleId, separated, gradient, parameters, previousGradient=null
}) {
  assertProjectionAllowed(tentacleId,separated);
  validateParameters(parameters);
  if (!vec3(gradient)) throw new TypeError("Expected finite synthetic 3-vector");
  if (previousGradient!==null && !vec3(previousGradient)) throw new TypeError("Invalid prior recorded vector");
  if (tentacleId==="T7_TIME" && previousGradient===null) throw new TypeError("Recorded history required for T7");
  const g=[...gradient],theta=parameters.knifeEdgeAngleDeg*Math.PI/180;
  const knife=[Math.cos(theta),Math.sin(theta),0];
  const directional=dot(unit(g),knife);
  const base=tentacleId==="T7_TIME"
    ? norm(g.map((v,i)=>v-previousGradient[i]))
    : projection[tentacleId](g);
  const thresholded=Math.abs(base)<parameters.threshold?0:base;
  const signal=clamp(thresholded*directional*parameters.sensitivity*
    parameters.contrast*parameters.intensity,-1,1);
  if (!finite(signal)) throw new RangeError("Non-finite visual signal");
  return Object.freeze({
    schema:"scandoc-gradient-projection/1",
    tentacleId,
    domain:"SYNTHETIC_STATE_GRADIENT",
    synthetic:true,
    signal,
    // Persistence is renderer-only; it cannot synthesize missing recorded frames.
    persistence:parameters.persistence
  });
}
