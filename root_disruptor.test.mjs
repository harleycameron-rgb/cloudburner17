import {test} from 'node:test';import assert from 'node:assert/strict';import {fixture,move,disrupt,diagnose} from './root_disruptor.mjs';
test('common large motion is not drift',()=>assert.equal(diagnose(fixture(),move(fixture(),[2000,-500,12])).classification,'SUPPORTED_BY_FIXTURE'));
test('known disruptor is detected',()=>assert.ok(diagnose(fixture(),disrupt(move(fixture(),[2000,0,0]))).faults.includes('SHARED_TRANSFORM_BREACH:gain')));
test('cube mutation rejected',()=>{let a=fixture();assert.ok(diagnose(a,{...a,cube:{...a.cube,snapshot1536:'f'.repeat(384)}}).faults.includes('CUBE_SNAPSHOT_CHANGED'))});
test('gate mutation rejected',()=>{let a=fixture();assert.ok(diagnose(a,{...a,nativeGate:'OPEN'}).faults.includes('GATE_CHANGED'))});
test('nonfinite transform rejected',()=>assert.throws(()=>move(fixture(),[NaN,0,0])));
test('no source writes or authority',()=>{let r=diagnose(fixture(),disrupt(fixture()));assert.equal(r.sourceModified,false);assert.equal(r.writesPermitted,false);assert.equal(r.snapshotTrust,'UNVERIFIED')});
