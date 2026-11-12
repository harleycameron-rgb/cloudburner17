// Read-only synthetic root canary. Never an engine firing or a verified 1536 event.
export const CANARY_ID='SCANDOC-ROOT-DISRUPTOR-V1';
const names=['tap','surface','gain','habitat','engine','business','time-axis','foretentacle'];
const vec=v=>Array.isArray(v)&&v.length===3&&v.every(Number.isFinite);
const distance=(a,b)=>Math.hypot(...a.map((x,i)=>x-b[i]));
export function fixture(){return {id:CANARY_ID,source:'SYNTHETIC_FIXTURE',nativeGate:'CLOSED',cube:{snapshot1536:'0'.repeat(384),sentinel:'SYNTHETIC_UNVERIFIED',faces:names.slice(0,6)},tick:0,translation:[0,0,0],arms:names.map((name,i)=>({name,position:[Math.cos(i*Math.PI/4),Math.sin(i*Math.PI/4),i<6?0:0.25]}))};}
export function move(s,t){if(!vec(t))throw Error('invalid transform');const d=t.map((x,i)=>x-s.translation[i]);return {...s,tick:s.tick+1,translation:t,arms:s.arms.map(a=>({...a,position:a.position.map((x,i)=>x+d[i])}))};}
export function disrupt(s,name='gain',delta=.125){if(!Number.isFinite(delta))throw Error('invalid disruption');return {...s,arms:s.arms.map(a=>a.name===name?{...a,position:[a.position[0]+delta,...a.position.slice(1)]}:a)};}
export function diagnose(base,observed,epsilon=1e-9){if(!Number.isFinite(epsilon)||epsilon<0)throw Error('invalid epsilon');const faults=[];
if(base.source!=='SYNTHETIC_FIXTURE'||observed.source!=='SYNTHETIC_FIXTURE')faults.push('SOURCE_UNTRUSTED');
if(observed.nativeGate!=='CLOSED')faults.push('GATE_CHANGED');
if(JSON.stringify(base.cube)!==JSON.stringify(observed.cube))faults.push('CUBE_SNAPSHOT_CHANGED');
if(!Number.isSafeInteger(observed.tick)||observed.tick<base.tick)faults.push('TICK_INVALID');
if(!vec(observed.translation)||!Array.isArray(observed.arms)||observed.arms.length!==8||observed.arms.some(a=>!vec(a.position)))faults.push('GEOMETRY_INVALID');
if(!faults.includes('GEOMETRY_INVALID')){const d=observed.translation.map((x,i)=>x-base.translation[i]);for(let i=0;i<8;i++){if(observed.arms[i].name!==base.arms[i].name){faults.push('ARM_ID_CHANGED');continue;}if(distance(observed.arms[i].position,base.arms[i].position.map((x,j)=>x+d[j]))>epsilon)faults.push('SHARED_TRANSFORM_BREACH:'+observed.arms[i].name);}for(let i=0;i<8;i++)for(let j=i+1;j<8;j++)if(Math.abs(distance(observed.arms[i].position,observed.arms[j].position)-distance(base.arms[i].position,base.arms[j].position))>epsilon){faults.push('PAIRWISE_DRIFT');i=8;break;}}
return Object.freeze({canaryId:CANARY_ID,classification:faults.length?'DISPROVEN_BY_FIXTURE':'SUPPORTED_BY_FIXTURE',faults:[...new Set(faults)],evidence:'SYNTHETIC_ONLY',snapshotTrust:'UNVERIFIED',nativeGate:'CLOSED',sourceModified:false,writesPermitted:false});}
