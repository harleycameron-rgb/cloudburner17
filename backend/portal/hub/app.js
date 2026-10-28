import {verifyReceipt, MAX_RECEIPT_BYTES} from './receipt.js';
'use strict';
const $=id=>document.getElementById(id), legs=['tap','surface','gain','habitat','engine','business'];
let receipt=null, revision=0;
function clearReceipt(){receipt=null;$('download').disabled=true;$('path').replaceChildren();}
function showReceipt(checked){receipt=checked;$('result').textContent=JSON.stringify(checked,null,2);plot(checked.result.trajectory);$('download').disabled=false;}

function reset(){revision++;clearReceipt();$('import-receipt').value=''; $('payload').value=JSON.stringify({legs:Object.fromEntries(legs.map((k,i)=>[k,[i*.01,0,0]])),tolerance:.5,samples:[{tick:0,center:[.025,0,0]},{tick:1,center:[.15,.1,0]},{tick:2,center:[.25,.08,0]}]},null,2); receipt=null;$('download').disabled=true;$('result').textContent='No response yet.';$('run-status').textContent='Synthetic inputs loaded.'; }
reset();$('reset').onclick=reset;
(async()=>{try{const r=await fetch('/integration/status',{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);const d=await r.json();if(d.schema!=='waxtablet-integration/1'||d.liveGate!=='CLOSED'||d.sphereWrites!==false)throw Error('Unexpected application contract');$('connection').textContent='Connected: terminal, audit, supervisor and trajectory lab · research mode · live gate CLOSED';}catch(e){$('connection').textContent='Connection unavailable: '+e.message;}})();
$('run').onclick=async()=>{const current=++revision;clearReceipt();$('import-receipt').disabled=true;$('run').disabled=true;$('run-status').textContent='Validating supplied inputs…';try{const body=JSON.parse($('payload').value);const r=await fetch('/integration/research-run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const d=await r.json();if(!r.ok)throw Error(typeof d.detail==='string'?d.detail:JSON.stringify(d.detail));const checked=await verifyReceipt(d);if(current!==revision)return;const replay=await fetch('/integration/verify-research-run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(checked)});const verified=await replay.json();if(!replay.ok||verified.schema!=='waxtablet-research-verification/1'||verified.replayConsistent!==true||verified.contentIntegrity!==true||verified.sha512!==checked.sha512||verified.liveGate!=='CLOSED'||verified.sphereWrites!==false||verified.receiptTrust!=='UNVERIFIED'||verified.stored!==false)throw Error('Research replay verification failed');if(current!==revision)return;showReceipt(checked);$('run-status').textContent='Integrity and server replay checked · '+checked.result.trajectory.length+' supplied samples · unsigned / UNVERIFIED · no live write';}catch(e){if(current!==revision)return;clearReceipt();$('run-status').textContent='Blocked: '+e.message;$('result').textContent='No receipt issued for rejected inputs.';$('path').replaceChildren();}finally{$('run').disabled=false;$('import-receipt').disabled=false;}};
function plot(samples){const svg=$('path'),ns='http://www.w3.org/2000/svg',raw=samples.map(p=>p[1]),scale=Math.max(1,...raw.flatMap(p=>[Math.abs(p[0]),Math.abs(p[1])])),points=raw.map(p=>p.map(v=>v/scale));const xs=points.map(p=>p[0]),ys=points.map(p=>p[1]),minX=Math.min(...xs),minY=Math.min(...ys),dx=Math.max(...xs)-minX||1,dy=Math.max(...ys)-minY||1;svg.replaceChildren();const line=document.createElementNS(ns,'polyline');line.setAttribute('points',points.map(p=>`${40+(p[0]-minX)/dx*420},${300-(p[1]-minY)/dy*240}`).join(' '));line.setAttribute('fill','none');line.setAttribute('stroke','#7de4e9');line.setAttribute('stroke-width','3');svg.append(line);for(let i=0;i<points.length;i++){const c=document.createElementNS(ns,'circle');c.setAttribute('cx',40+(points[i][0]-minX)/dx*420);c.setAttribute('cy',300-(points[i][1]-minY)/dy*240);c.setAttribute('r',5);c.setAttribute('fill','#e8bd6a');svg.append(c);}const label=document.createElementNS(ns,'text');label.setAttribute('x','25');label.setAttribute('y','25');label.textContent='SUPPLIED SAMPLES / XY PROJECTION / UNVERIFIED';svg.append(label);}
$('download').onclick=()=>{if(!receipt)return;const blob=new Blob([JSON.stringify(receipt,null,2)+'\n'],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='waxtablet-research-receipt.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};

$('import-receipt').onchange=async()=>{
  const file=$('import-receipt').files[0];
  if(!file)return;
  const current=++revision;clearReceipt();
  $('result').textContent='Checking local receipt…';
  $('run-status').textContent='Checking local receipt…';
  try{
    if(file.size>MAX_RECEIPT_BYTES)throw Error('Receipt exceeds the 2 MiB limit');
    const checked=await verifyReceipt(JSON.parse(await file.text()));
    if(current!==revision)return;
    showReceipt(checked);
    $('run-status').textContent='Local receipt integrity checked · unsigned / UNVERIFIED · no upload';
  }catch(error){
    if(current!==revision)return;
    clearReceipt();$('result').textContent='No verified receipt loaded.';
    $('run-status').textContent='Blocked: '+error.message;
  }
};
