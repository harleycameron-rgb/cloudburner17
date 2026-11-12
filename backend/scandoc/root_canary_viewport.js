import {CANARY_ID,fixture,move,disrupt,diagnose} from '../../root_disruptor.mjs';
export function mountRootCanary(doc=document){
 const el=id=>doc.getElementById(id),canvas=el('root-canary-canvas'),status=el('root-canary-status'),output=el('root-canary-result');
 if(!canvas||!status||!output)return ()=>{};
 const ctx=canvas.getContext('2d');if(!ctx){status.textContent='Canvas unavailable; diagnostic disabled';return ()=>{}}
 const base=fixture();let current=base,tick=0;let injected=false;
 const paint=()=>{
  const report=diagnose(base,current);const w=canvas.width,h=canvas.height;
  ctx.fillStyle='#061321';ctx.fillRect(0,0,w,h);
  ctx.font='13px monospace';ctx.fillStyle='#a6c8db';ctx.fillText('ROOT CANARY / '+CANARY_ID,12,20);
  const t=current.translation;const center=[w*.5,h*.52];const scale=65;
  ctx.strokeStyle='#436477';ctx.beginPath();ctx.arc(...center,scale,0,Math.PI*2);ctx.stroke();
  for(let i=0;i<current.arms.length;i++){
   const a=current.arms[i],p=a.position.map((v,j)=>v-t[j]);
   const x=center[0]+p[0]*scale,y=center[1]-p[1]*scale;
   ctx.fillStyle=a.name==='gain'?'#e8b478':'#7ed4e4';ctx.beginPath();ctx.arc(x,y,4,0,Math.PI*2);ctx.fill();
   ctx.fillStyle='#c2d9e5';ctx.fillText(a.name,x+5,y-5);
  }
  ctx.fillStyle=report.faults.length?'#f6a3a3':'#9bdab8';ctx.fillText(report.classification,12,h-16);
  status.textContent=(report.faults.length?'DRIFT DETECTED':'NO STRUCTURAL DRIFT DETECTED')+' · '+(injected?'IDENTIFIED DISRUPTOR ACTIVE':'CONTROL')+' · synthetic only';
  output.textContent=JSON.stringify({...report,tick:current.tick,translation:current.translation,referenceSnapshot:base.cube.snapshot1536.slice(0,12)+'…',referenceUnchanged:true},null,2);
 };
 const interval=setInterval(()=>{tick++;current=move(base,[tick*.012,Math.sin(tick*.025)*.2,0]);if(injected)current=disrupt(current);paint()},200);
 el('root-canary-inject')?.addEventListener('click',()=>{injected=true;paint()});
 el('root-canary-clear')?.addEventListener('click',()=>{injected=false;paint()});
 paint();return ()=>clearInterval(interval);
}
