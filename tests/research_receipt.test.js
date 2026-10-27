import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {verifyReceipt} from '../backend/portal/hub/receipt.js';
const closed={liveGate:'CLOSED',sphereWrites:false,receiptTrust:'UNVERIFIED'};
function receipt(change=()=>{}){
  const record={schema:'waxtablet-research-run/1',kind:'supplied-sample-research',
    separation:{...closed},result:{...closed,trajectory:[[0,[0,0,0]],[1,[.1,0,0]]]},
    ...closed,stored:false};
  change(record);
  const canonicalRecord=JSON.stringify(record);
  return {...record,canonicalRecord,sha512:createHash('sha512').update('waxtablet-research-run/1\0'+canonicalRecord).digest('hex')};
}
test('accepts a consistent unsigned closed receipt and returns a detached record',async()=>{
  const input=receipt(),checked=await verifyReceipt(input);
  assert.deepEqual(checked,input);input.result.trajectory[0][1][0]=8;
  assert.equal(checked.result.trajectory[0][1][0],0);
});
test('rejects changed display content even with the original valid hash',async()=>{
  const input=receipt();input.result.trajectory[1][1][0]=9;
  await assert.rejects(verifyReceipt(input),/differs/);
});
test('rejects a changed hash',async()=>{
  const input=receipt();input.sha512='0'.repeat(128);
  await assert.rejects(verifyReceipt(input),/mismatch/);
});
test('rejects unsupported fields and old receipts without exact bytes',async()=>{
  const extra=receipt();extra.authenticated=true;
  await assert.rejects(verifyReceipt(extra),/envelope/);
  const old=receipt();delete old.canonicalRecord;
  await assert.rejects(verifyReceipt(old),/envelope/);
});
test('rejects live-write claims at every boundary',async()=>{
  for(const mutate of [r=>r.sphereWrites=true,r=>r.result.liveGate='OPEN',r=>r.separation.receiptTrust='VERIFIED',r=>r.stored=true]){
    await assert.rejects(verifyReceipt(receipt(mutate)),/contract/);
  }
});
test('rejects malformed, nonmonotonic or excessive trajectories even if rehashed',async()=>{
  for(const samples of [[],[[0,[0,0,0]]],[[0,[0,0,0]],[0,[1,0,0]]],[[0,[0,0,0]],[1,[1,0]]],Array.from({length:513},(_,i)=>[i,[0,0,0]])]){
    await assert.rejects(verifyReceipt(receipt(r=>r.result.trajectory=samples)),/trajectory/);
  }
});
test('binds original serialization rather than reserializing Python floats',async()=>{
  const input=receipt();input.canonicalRecord=input.canonicalRecord.replace('"stored":false','"stored": false');
  input.sha512=createHash('sha512').update('waxtablet-research-run/1\0'+input.canonicalRecord).digest('hex');
  await verifyReceipt(input);
});
test('captures the checked state before asynchronous digest work',async()=>{
  const input=receipt(),pending=verifyReceipt(input);input.result.trajectory[1][1][0]=9;
  assert.equal((await pending).result.trajectory[1][1][0],.1);
});
