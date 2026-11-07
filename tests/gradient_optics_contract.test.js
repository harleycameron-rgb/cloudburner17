import test from "node:test";
import assert from "node:assert/strict";
import {validateGradientState,validateParameters,assertProjectionAllowed,TENTACLES} from "../src/gradient_optics_contract.js";
const preset={sensitivity:.6,knifeEdgeAngleDeg:45,threshold:.25,contrast:1.5,persistence:.35,intensity:.8};
const expected={firingId:"existing",topologyCommitment:"immutable"};
const state=()=>({
 schema:"scandoc-gradient-optics-state/1",moduleVersion:"scandoc-gradient-optics/1",
 controlsVersion:"scandoc-controls/3",sessionVersion:"scandoc-session/2",
 firingId:"existing",topologyCommitment:"immutable",
 input:{inputId:"synthetic",mode:"SYNTHETIC_GEOMETRY",domain:"SYNTHETIC_STATE_GRADIENT",provenance:"SYNTHETIC_SIMULATION",accessState:"MANUAL"},
 sharedPreset:{...preset},localOverrides:{T1_TAP:{knifeEdgeAngleDeg:30}},nativeGate:"CLOSED"
});
test("accepts matching synthetic filter state",()=>assert.equal(validateGradientState(state(),expected),true));
test("rejects changed firing and topology",()=>{
 for (const field of ["firingId","topologyCommitment"]) {
  const s=state();s[field]="other";
  assert.throws(()=>validateGradientState(s,expected));
 }
});
test("rejects gate opening",()=>{const s=state();s.nativeGate="OPEN";assert.throws(()=>validateGradientState(s,expected));});
test("rejects provenance spoofing",()=>{
 for(const field of ["mode","domain","provenance"]) {
  const s=state();s.input[field]="OPTICAL_MEASURED";
  assert.throws(()=>validateGradientState(s,expected));
 }
});
test("rejects NaN, Infinity, out-of-range and unknown settings",()=>{
 for(const v of [NaN,Infinity,-1,2]) assert.throws(()=>validateParameters({...preset,sensitivity:v}));
 assert.throws(()=>validateParameters({...preset,unexpected:1}));
});
test("all six launch legs permitted, two temporal legs gated",()=>{
 for(const id of TENTACLES.slice(0,6)) assert.equal(assertProjectionAllowed(id,false),true);
 for(const id of TENTACLES.slice(6)) {
  assert.throws(()=>assertProjectionAllowed(id,false));
  assert.equal(assertProjectionAllowed(id,true),true);
 }
});
test("rejects unknown overrides and extra fields",()=>{
 const s=state();s.localOverrides.UNKNOWN={sensitivity:.5};
 assert.throws(()=>validateGradientState(s,expected));
 const x=state();x.rawCameraData="not allowed";
 assert.throws(()=>validateGradientState(x,expected));
});
