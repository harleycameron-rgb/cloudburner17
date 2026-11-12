// Synthetic Tentacle 7 trace recorder. No native firing, persistence, or external data.
import {createHash} from 'node:crypto';
import {fixture,move,diagnose} from '../../backend/scandoc/root_disruptor.mjs';
const hash=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
export function recordTrace(translations=[[0.1,0,0],[0.2,0.1,0],[0.3,0.1,0.2]]){
 const base=fixture(); const origin={kind:'SEPARATION',tick:0,translation:[0,0,0],cubeDigest:hash(base.cube),source:'SYNTHETIC_UNVERIFIED'};
 const events=[];let previous='GENESIS_UNVERIFIED',current=base;
 for(const payload of [origin,...translations.map((translation,i)=>({kind:'SPHERE_TRANSLATION',tick:i+1,translation}))]){
  if(payload.kind==='SPHERE_TRANSLATION')current=move(current,payload.translation);
  const event={...payload,previousHash:previous};event.eventHash=hash(event);previous=event.eventHash;
  events.push(event);
 }
 return {schema:'SCANDOC-T7-TRACE-SYNTHETIC-V1',nativeGate:'CLOSED',writesPermitted:false,snapshotTrust:'UNVERIFIED',events,reference:base,final:current,diagnostic:diagnose(base,current)};
}
export function verifyTrace(trace){
 if(trace?.schema!=='SCANDOC-T7-TRACE-SYNTHETIC-V1'||!Array.isArray(trace.events)||trace.events.length<1)return {valid:false,reason:'SCHEMA'};
 const base=fixture();let state=base,previous='GENESIS_UNVERIFIED';
 for(let i=0;i<trace.events.length;i++){
  const {eventHash,...event}=trace.events[i];
  if(event.previousHash!==previous||hash(event)!==eventHash)return {valid:false,reason:'HASH_CHAIN',index:i};
  if(i===0){if(event.kind!=='SEPARATION'||event.tick!==0||event.cubeDigest!==hash(base.cube))return {valid:false,reason:'SEPARATION'};}
  else {
   if(event.kind!=='SPHERE_TRANSLATION'||event.tick!==i||!Array.isArray(event.translation)||event.translation.length!==3||!event.translation.every(Number.isFinite))return {valid:false,reason:'EVENT'};
   state=move(state,event.translation);
  }
  previous=eventHash;
 }
 if(trace.nativeGate!=='CLOSED'||trace.writesPermitted!==false)return {valid:false,reason:'GATE'};
 if(JSON.stringify(state)!==JSON.stringify(trace.final))return {valid:false,reason:'FINAL_MISMATCH'};
 return {valid:true,recordedEvents:trace.events.length,lastTick:state.tick,head:previous,classification:diagnose(base,state).classification};
}
if(import.meta.url===`file://${process.argv[1]}`){
 const trace=recordTrace();const verification=verifyTrace(trace);
 const tampered=structuredClone(trace);tampered.events[1].translation[0]=999;
 const tamperResult=verifyTrace(tampered);
 const futureRejected=trace.events.every((e,i)=>e.tick===i)&&verification.lastTick===trace.events.length-1;
 const result={fixtureOnly:true,verification,tamperResult,futureRejected,gate:trace.nativeGate};
 console.log(JSON.stringify(result,null,2));
 if(!verification.valid||tamperResult.valid||!futureRejected||verification.classification!=='SUPPORTED_BY_FIXTURE')process.exitCode=1;
}
