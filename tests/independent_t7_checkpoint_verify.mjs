// Independent checkpoint verifier for synthetic T7 traces.
// Does not import the recorder. Requires an externally held signed checkpoint.
import {readFileSync} from 'node:fs';
import {createHash,verify as verifySignature,createPublicKey} from 'node:crypto';
const sha=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const fail=reason=>({verified:false,reason});
export function verifyIndependent(trace,checkpoint,publicKeyPem){
 if(!trace||!checkpoint||typeof publicKeyPem!=='string')return fail('MISSING_INPUT');
 if(trace.schema!=='SCANDOC-T7-TRACE-SYNTHETIC-V1'||trace.nativeGate!=='CLOSED'||trace.writesPermitted!==false||trace.snapshotTrust!=='UNVERIFIED')return fail('TRACE_SCHEMA');
 if(checkpoint.schema!=='SCANDOC-T7-CHECKPOINT-V1'||checkpoint.lineage!=='SYNTHETIC_UNVERIFIED'||checkpoint.algorithm!=='Ed25519')return fail('CHECKPOINT_SCHEMA');
 if(!Array.isArray(trace.events)||trace.events.length<1||!Number.isSafeInteger(checkpoint.acceptedFrontier)||checkpoint.acceptedFrontier<0)return fail('FRONTIER');
 if(trace.events.length-1!==checkpoint.acceptedFrontier)return fail('FRONTIER_MISMATCH');
 if(typeof checkpoint.head!=='string'||!/^[0-9a-f]{64}$/.test(checkpoint.head)||typeof checkpoint.signature!=='string')return fail('CHECKPOINT_FORMAT');
 // Signature covers the exact canonical payload fields below, never the signature itself.
 const signed={schema:checkpoint.schema,lineage:checkpoint.lineage,algorithm:checkpoint.algorithm,acceptedFrontier:checkpoint.acceptedFrontier,head:checkpoint.head};
 let key;
 try{key=createPublicKey(publicKeyPem);if(key.asymmetricKeyType!=='ed25519')return fail('KEY_TYPE');
 if(!verifySignature(null,Buffer.from(JSON.stringify(signed)),key,Buffer.from(checkpoint.signature,'base64')))return fail('SIGNATURE');}
 catch{return fail('SIGNATURE_OR_KEY');}
 let prev='GENESIS_UNVERIFIED';
 for(let i=0;i<trace.events.length;i++){
  const {eventHash,...payload}=trace.events[i];
  if(payload.previousHash!==prev||payload.tick!==i||sha(payload)!==eventHash)return fail('CHAIN');
  if(i===0&&(payload.kind!=='SEPARATION'||payload.source!=='SYNTHETIC_UNVERIFIED'||JSON.stringify(payload.translation)!=='[0,0,0]'))return fail('SEPARATION');
  if(i>0&&(payload.kind!=='SPHERE_TRANSLATION'||!Array.isArray(payload.translation)||payload.translation.length!==3||!payload.translation.every(Number.isFinite)))return fail('EVENT');
  prev=eventHash;
 }
 if(prev!==checkpoint.head)return fail('HEAD_MISMATCH');
 return {verified:true,scope:'SIGNED_SYNTHETIC_TRACE_ONLY',acceptedFrontier:checkpoint.acceptedFrontier,head:prev,nativeGate:'CLOSED'};
}
if(process.argv[1]&&import.meta.url===new URL('file://'+process.argv[1]).href){
 if(process.argv.length!==5){console.error('Usage: node independent_t7_checkpoint_verify.mjs trace.json checkpoint.json trusted-public-key.pem');process.exit(2);}
 const result=verifyIndependent(JSON.parse(readFileSync(process.argv[2],'utf8')),JSON.parse(readFileSync(process.argv[3],'utf8')),readFileSync(process.argv[4],'utf8'));
 console.log(JSON.stringify(result,null,2));if(!result.verified)process.exitCode=1;
}
