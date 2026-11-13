import test from 'node:test';
import assert from 'node:assert/strict';
import {observeExterior} from '../backend/scandoc/exterior_observer.mjs';
test('observer is deterministic, read-only and keeps original event IDs',()=>{
 const input=[{sequence:0,eventID:'sep',position:[0,0,0]},{sequence:1,eventID:'a',position:[1,0,0]}];
 const original=JSON.stringify(input);
 const a=observeExterior(input);
 assert.deepEqual(a,observeExterior(input));
 assert.equal(JSON.stringify(input),original);
 assert.deepEqual(a.sourceEventIDs,['sep','a']);
 assert.equal(a.drift[0].distance,1);
 assert.equal(a.nativeGate,'CLOSED');assert.equal(a.writesPermitted,false);
 assert.equal(a.evidenceState,'UNKNOWN');
});
test('invalid geometry and gaps are detected, never promoted to supported',()=>{
 const x=observeExterior([{sequence:1,eventID:'x',position:[NaN,0,0]}]);
 assert.deepEqual(x.anomalies.map(a=>a.code),['SEQUENCE_GAP','NONFINITE_GEOMETRY']);
 assert.equal(x.evidenceState,'UNKNOWN');
});
test('sparse coordinates are rejected as invalid geometry',()=>{
 const x=observeExterior([{sequence:0,eventID:'sparse',position:[1,,0]}]);
 assert.deepEqual(x.trace,[]);
 assert.deepEqual(x.anomalies,[{code:'NONFINITE_GEOMETRY',eventID:'sparse'}]);
});
test('non-finite drift distances are reported instead of recorded',()=>{
 const x=observeExterior([
  {sequence:0,eventID:'left',position:[-1e308,0,0]},
  {sequence:1,eventID:'right',position:[1e308,0,0]}
 ]);
 assert.deepEqual(x.drift,[]);
 assert.deepEqual(x.anomalies,[{code:'NONFINITE_DRIFT',from:'left',to:'right'}]);
});
test('rejects invalid tolerances',()=>assert.throws(()=>observeExterior([], {tolerance:-1})));
