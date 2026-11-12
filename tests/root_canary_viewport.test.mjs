import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mountRootCanary} from '../backend/scandoc/root_canary_viewport.js';
test('viewport: control, shared motion, immediate disrupt and clear, immutable reference',()=>{
 let advance;const previous=globalThis.setInterval,previousClear=globalThis.clearInterval;
 globalThis.setInterval=fn=>(advance=fn,1);globalThis.clearInterval=()=>{};
 try {
 const ctx={fillRect(){},beginPath(){},arc(){},stroke(){},fill(){},fillText(){}};
 const ids=['root-canary-canvas','root-canary-status','root-canary-result','root-canary-inject','root-canary-clear'];
 const nodes=Object.fromEntries(ids.map(id=>[id,{textContent:'',width:760,height:330,getContext:()=>ctx,addEventListener(_,fn){this.click=fn}}]));
 const stop=mountRootCanary({getElementById:id=>nodes[id]});
 const result=()=>JSON.parse(nodes['root-canary-result'].textContent);
 assert.equal(result().classification,'SUPPORTED_BY_FIXTURE');
 const reference=result().referenceSnapshot;
 for(let i=0;i<100;i++)advance();
 assert.equal(result().classification,'SUPPORTED_BY_FIXTURE');
 const tick=result().tick;
 nodes['root-canary-inject'].click();
 assert.ok(result().faults.includes('SHARED_TRANSFORM_BREACH:gain'));
 assert.ok(result().faults.includes('PAIRWISE_DRIFT'));
 assert.equal(result().tick,tick);
 nodes['root-canary-clear'].click();
 assert.equal(result().classification,'SUPPORTED_BY_FIXTURE');
 assert.equal(result().tick,tick);
 assert.equal(result().referenceSnapshot,reference);
 assert.equal(result().sourceModified,false);
 assert.equal(result().writesPermitted,false);
 stop();
 }finally{globalThis.setInterval=previous;globalThis.clearInterval=previousClear}
});
