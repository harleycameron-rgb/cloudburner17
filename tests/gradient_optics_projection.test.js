import test from "node:test";
import assert from "node:assert/strict";
import {projectSyntheticGradient} from "../src/gradient_optics_projection.js";
import {TENTACLES} from "../src/gradient_optics_contract.js";
const p={sensitivity:.8,knifeEdgeAngleDeg:45,threshold:.1,contrast:1.2,persistence:.2,intensity:.9};
const request=(id,extra={})=>({tentacleId:id,separated:true,gradient:[.4,.5,.6],parameters:p,...extra});
test("all eight produce finite synthetic signals",()=>{
 for(const id of TENTACLES){
  const result=projectSyntheticGradient(request(id,{previousGradient:[.1,.2,.3]}));
  assert.equal(result.synthetic,true);
  assert.equal(result.domain,"SYNTHETIC_STATE_GRADIENT");
  assert.ok(Number.isFinite(result.signal));
  assert.ok(Math.abs(result.signal)<=1);
 }
});
test("inputs and filter parameters are never mutated",()=>{
 const gradient=[.4,.5,.6],parameters={...p};
 projectSyntheticGradient(request("T1_TAP",{gradient,parameters}));
 assert.deepEqual(gradient,[.4,.5,.6]);
 assert.deepEqual(parameters,p);
});
test("post-separation gates reject early projection",()=>{
 for(const id of TENTACLES.slice(6)) assert.throws(()=>projectSyntheticGradient(request(id,{separated:false,previousGradient:[0,0,0]})));
});
test("T7 requires actual prior recorded gradient",()=>{
 assert.throws(()=>projectSyntheticGradient(request("T7_TIME")));
 assert.equal(projectSyntheticGradient(request("T7_TIME",{previousGradient:[0,0,0]})).synthetic,true);
});
test("rejects invalid vectors, invalid controls and non-finite data",()=>{
 for(const gradient of [[1,2],[NaN,0,0],[Infinity,0,0],null]) assert.throws(()=>projectSyntheticGradient(request("T1_TAP",{gradient})));
 assert.throws(()=>projectSyntheticGradient(request("T1_TAP",{parameters:{...p,intensity:2}})));
});
test("output depends on local tentacle geometry",()=>{
 const values=TENTACLES.slice(0,6).map(id=>projectSyntheticGradient(request(id)).signal);
 assert.ok(new Set(values).size>1);
});
