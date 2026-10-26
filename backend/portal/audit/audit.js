"use strict";
const blocked=new Set(["apply-centre","fire-sentinel","undo-sentinel","complete-separation","start-trajectory"]);
const ids=["tap","surface","spiritlevel","gain","habitat","time","space","lineage"];
const counts=Object.create(null);
function summarize(event,origin,frames){
 if(event.origin!==origin||!event.data||typeof event.data!=="object")return null;
 const d=event.data,id=d.acknowledgement?.appId||d.feed?.appId||d.appId;
 if(!ids.includes(id)||frames.get(id)!==event.source||!["sphere:ack","sphere:feed","sphere:feed-clear"].includes(d.type))return null;
 return {appId:id,type:d.type};
}
if(typeof module!=="undefined")module.exports={summarize};
if(typeof document!=="undefined"){
 document.addEventListener("click",e=>{const b=e.target.closest?.("button");if(b&&blocked.has(b.id)){e.preventDefault();e.stopImmediatePropagation();}},true);
 document.addEventListener("DOMContentLoaded",()=>{
  const panel=document.createElement("aside");panel.style.cssText="padding:1rem;margin:1rem;border:2px solid orange;background:#132033;color:white";
  const text=document.createElement("p");text.textContent="SOURCE-AUDIT PREVIEW, NOT COMPLETED WAXTABLET. Upstream eight-arm geometry is retained for inspection, not accepted as the owner architecture. Space/Lineage values require the recorded separation trajectory to be plotted. No real upstream firing, recorder or melt consumer is connected by this wrapper. Fire/shift/separation controls disabled. Camera/orientation/audio remain explicit local user gestures.";
  const link=document.createElement("a");link.href="/source-manifest.json";link.textContent="Pinned public-source manifest";
  const pre=document.createElement("pre");pre.textContent="Frame-message counts only; not trajectory recording or proof: {}";
  panel.append(text,link,pre);document.body.prepend(panel);
  function disable(){for(const id of blocked){const b=document.getElementById(id);if(b&&!b.disabled)b.disabled=true;}}
  new MutationObserver(disable).observe(document.documentElement,{subtree:true,childList:true,attributes:true,attributeFilter:["disabled"]});disable();
  window.addEventListener("message",event=>{
   const frames=new Map();for(const f of document.querySelectorAll("iframe.app-frame")){try{const u=new URL(f.src,location.href),m=u.pathname.match(/^\/apps\/([a-z]+)\.html$/);if(u.origin===location.origin&&m)frames.set(m[1],f.contentWindow);}catch(_){}}
   const value=summarize(event,location.origin,frames);if(!value)return;
   const key=value.appId+":"+value.type;counts[key]=Math.min(1000000,(counts[key]||0)+1);pre.textContent="Frame-message counts only; not trajectory recording or proof: "+JSON.stringify(counts,null,2);
  });
 },{once:true});
}
