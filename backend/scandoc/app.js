import { syntheticDemo, contextSeed, createController, nextProposal, toCSV } from "./model.js";

const $ = id => document.getElementById(id);
let demo, controller;
let pending = false;
const controls = ["json", "csv", "context", "proposal", "example"];
const show = value => { $("output").textContent = JSON.stringify(value, null, 2); };
function setPending(value) {
  pending = value;
  $("demo").disabled = value;
  $("result").disabled = value;
  for (const id of controls) $(id).disabled = value || !controller;
  $("status").setAttribute("aria-busy", String(value));
}
function invalidate(error) {
  demo = undefined;
  controller = undefined;
  $("status").textContent = `${error.code ?? "INVALID_INPUT"}: ${error.message}. Previous displayed results are STALE; rerun the local demo.`;
  $("summary").textContent = "STALE — no current export or proposal context.";
  $("geometry-data").textContent = "STALE — geometry from the prior run is not current.";
  $("output").textContent = "STALE — " + $("output").textContent;
  $("result").value = "";
}
function summary() {
  const state = demo.trajectory.at(-1), units = demo.model.frame.units;
  $("summary").textContent = [
    "SYNTHETIC ONLY — current local run",
    `Cube SHA-512: ${demo.cubeDigest}`,
    `Trajectory SHA-512: ${demo.trajectoryDigest}`,
    `Tick/time: ${state.tick} / ${state.time} ${units.time}`,
    `Sphere geometric radius: ${state.sphere.radius} ${units.length}`,
    `Center distance from declared radius origin: ${demo.centerDistanceFromRadiusOrigin} ${units.length}`,
    `Center velocity: [${state.sphere.velocity.join(", ")}] ${units.length}/${units.time}`,
    `Synthetic phase frequency: ${demo.frequency.value} ${demo.frequency.units}`,
    `Median: ${demo.median} (dimensionless)`,
    `Boundary: ${demo.boundary.status} / ${demo.boundary.closure} / ${demo.boundary.motion}`,
    `c6/abs(v7): ${demo.boundary.ratio.value} (${demo.boundary.ratio.status})`,
    `Origin: ${demo.originStatus}; torsion: UNRESOLVED`,
  ].join("\n");
  $("geometry-data").textContent = JSON.stringify({
    synthetic: true, frame: demo.model.frame, cubeCenter: demo.model.baseline.C,
    faces: state.faces, vertices: demo.cubeState.geometry.vertices,
    sphere: state.sphere, sentinel: state.sentinel,
    trajectory: demo.trajectory.map(s => ({ tick: s.tick, time: s.time, sphere: s.sphere })),
  }, null, 2);
}
function draw() {
  const ctx = $("view").getContext("2d"), origin = demo.model.frame.origin;
  if (!ctx) return;
  const point = p => [310 + (p[0]-origin[0])*130 + (p[2]-origin[2])*45,
    210 - (p[1]-origin[1])*130 - (p[2]-origin[2])*45];
  ctx.clearRect(0, 0, 900, 420);
  const state = demo.trajectory.at(-1);
  ctx.font = "16px sans-serif";
  ctx.strokeStyle = "#7ab9ff";
  const geometry = demo.cubeState.geometry;
  for (const indices of geometry.faceVertices) {
    ctx.beginPath();
    indices.forEach((index, i) => {
      const p = point(geometry.vertices[index]);
      if (i) ctx.lineTo(...p); else ctx.moveTo(...p);
    });
    ctx.closePath();
    ctx.stroke();
  }
  ctx.beginPath();
  demo.trajectory.forEach((s, i) => {
    const p = point(s.sphere.center);
    if (i) ctx.lineTo(...p); else ctx.moveTo(...p);
  });
  ctx.stroke();
  for (const face of state.faces) {
    const p = point(face.position);
    ctx.fillStyle = "#7ab9ff";
    ctx.fillRect(p[0]-5, p[1]-5, 10, 10);
    ctx.fillText(face.id, p[0]+8, p[1]-8);
  }
  ctx.strokeStyle = "#ffb55a";
  ctx.beginPath();
  ctx.arc(...point(state.sphere.center), state.sphere.radius*130, 0, 2*Math.PI);
  ctx.stroke();
  ctx.fillStyle = "#fff";
  const sentinel = point(state.sentinel);
  ctx.fillRect(sentinel[0]-4, sentinel[1]-4, 8, 8);
  ctx.fillText("Sentinel / shared origin", sentinel[0]+8, sentinel[1]+24);
  ctx.fillText("SYNTHETIC · final sampled tick " + state.tick, 30, 30);
}
function download(content, name, type) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
$("demo").addEventListener("click", async () => {
  if (pending) return;
  demo = undefined;
  controller = undefined;
  setPending(true);
  $("status").textContent = "Local work pending; previous results are STALE.";
  $("summary").textContent = "STALE — generating a new synthetic run.";
  $("geometry-data").textContent = "STALE — waiting for current geometry.";
  $("output").textContent = "STALE — waiting for current output.";
  $("result").value = "";
  try {
    const generated = await syntheticDemo();
    const verified = await createController(generated, await contextSeed(generated));
    demo = generated;
    controller = verified;
    summary();
    draw();
    show({ ...demo, context: controller.requestContext() });
    $("status").textContent = "Synthetic demo complete. Measured evidence, origin hash and burn receipt: unresolved. Transmission disabled.";
  } catch (error) { invalidate(error); }
  finally { setPending(false); }
});
$("json").addEventListener("click", () => {
  if (!pending && controller) download(JSON.stringify({ ...demo, context: controller.requestContext() }, null, 2),
    "scandoc-synthetic.json", "application/json");
});
$("csv").addEventListener("click", () => {
  if (!pending && controller) download(toCSV(demo), "scandoc-synthetic.csv", "text/csv");
});
$("context").addEventListener("click", () => {
  if (!pending && controller) show(controller.requestContext());
});
$("example").addEventListener("click", () => {
  if (pending || !controller) return;
  $("result").value = JSON.stringify(nextProposal(controller.body), null, 2);
  $("status").textContent = "Exact next-state example generated from the current exported seed. NOT submitted; click verify explicitly.";
});
$("proposal").addEventListener("click", async () => {
  if (pending || !controller) return;
  setPending(true);
  $("status").textContent = "Local proposal validation pending; prior output is STALE.";
  try {
    const text = $("result").value;
    if (text.length > 1024*1024) throw new Error("Local proposal exceeds 1 MiB");
    show(await controller.suppliedFiringResult(JSON.parse(text)));
    $("status").textContent = "Forecast only. Observed prefix unchanged. No lifecycle authorization.";
  } catch (error) { invalidate(error); }
  finally { setPending(false); }
});


/* Parallel Chaos Lab: local observer-model study. NO coupling to native runtime.
 * The sole read-only source is a deterministic fixed reference field.
 * 'Candidate' means threshold discrepancy, never a proved false invariant. */
(() => {
  const el = id => document.getElementById(id);
  const source = el("lab-source"), sandbox = el("lab-sandbox");
  if (!source || !sandbox) return;
  const ctxA = source.getContext("2d"), ctxB = sandbox.getContext("2d");
  if (!ctxA || !ctxB) {
    document.querySelectorAll(".lab input, .lab button").forEach(control => {
      control.disabled = true;
    });
    el("lab-status").textContent = "Chaos Lab unavailable: a 2D canvas context could not be created.";
    return;
  }
  const N = 144;
  const baseline = Object.freeze(Array.from({length:N},(_,i) => {
    const t=i/(N-1);
    return 0.5+0.19*Math.sin(2*Math.PI*t*2)+0.08*Math.sin(2*Math.PI*t*7);
  }));
  let snapshot=null, splatted=false;
  const options=()=>({
    aperture:Number(el("lab-aperture").value)/100,
    distortion:Number(el("lab-distortion").value)/100,
    threshold:Number(el("lab-threshold").value)/100
  });
  function observed(opt) {
    return baseline.map((v,i)=>{
      const t=i/(N-1);
      // deterministic observer-side model distortion, never a source mutation
      return Math.min(1,Math.max(0,v+opt.distortion*(0.18*Math.sin(18*Math.PI*t+0.4)+0.10*Math.sin(37*Math.PI*t))));
    });
  }
  function setup(ctx){
    const {width:w,height:h}=ctx.canvas;
    ctx.clearRect(0,0,w,h);ctx.fillStyle="#05101e";ctx.fillRect(0,0,w,h);
    ctx.strokeStyle="#203b55";ctx.lineWidth=1;
    for(let j=1;j<5;j++){ctx.beginPath();ctx.moveTo(0,h*j/5);ctx.lineTo(w,h*j/5);ctx.stroke();}
  }
  function trace(ctx,series,color,clip=null){
    const w=ctx.canvas.width,h=ctx.canvas.height;
    ctx.save();if(clip){ctx.beginPath();ctx.rect(clip[0],0,clip[1],h);ctx.clip();}
    ctx.strokeStyle=color;ctx.lineWidth=2.5;ctx.beginPath();
    series.forEach((v,i)=>{const x=10+i/(N-1)*(w-20),y=(1-v)*(h-32)+16;if(!i)ctx.moveTo(x,y);else ctx.lineTo(x,y);});
    ctx.stroke();ctx.restore();
  }
  function metrics(observation,opt){
    const residuals=observation.map((v,i)=>Math.abs(v-baseline[i]));
    const candidates=residuals.filter(x=>x>opt.threshold).length;
    return {candidate_mismatches:candidates, total_samples:N,
      unresolved:candidates, confirmed_false_invariants:0,
      max_deviation:Math.max(...residuals).toFixed(4)};
  }
  function draw(){
    const opt=options(),w=source.width;
    setup(ctxA);setup(ctxB);
    trace(ctxA,baseline,"#63d5f4");
    const paneWidth=w*opt.aperture, left=(w-paneWidth)/2;
    ctxA.fillStyle="rgba(5,16,30,.84)";
    ctxA.fillRect(0,0,left,source.height);ctxA.fillRect(left+paneWidth,0,w,source.height);
    ctxA.strokeStyle="#ebbe7f";ctxA.strokeRect(left,2,paneWidth,source.height-4);
    ctxA.fillStyle="#d8f3ff";ctxA.font="14px monospace";ctxA.fillText("SENTINEL → READ ONLY",12,24);
    ctxB.font="14px monospace";ctxB.fillStyle="#cfb3ef";ctxB.fillText("PARALLEL / NO CORE WRITE",12,24);
    if(snapshot){
      const optSnap=snapshot.options, rendered=observed(optSnap);
      trace(ctxB,rendered,"#b48df4");
      if(splatted){
        const r=metrics(rendered,optSnap),h=sandbox.height;
        for(let i=0;i<N;i++){
          if(Math.abs(rendered[i]-baseline[i])<=optSnap.threshold)continue;
          const x=10+i/(N-1)*(sandbox.width-20);
          ctxB.strokeStyle=i%2?"#fa9a61":"#e35df2";
          ctxB.beginPath();ctxB.moveTo(x,(1-rendered[i])*(h-32)+16);
          ctxB.lineTo(x+(i%5-2)*6,(1-baseline[i])*(h-32)+16);
          ctxB.stroke();
        }
        el("lab-result").textContent=JSON.stringify({
          schema:"scandoc-observer-sandbox-preview/1", classification:"UNRESOLVED",
          ...r, source_modified:false, native_gate:"CLOSED",
          interpretation:"Discrepancy counts are illustrative threshold candidates, not verified false invariants"
        },null,2);
      }
    }
  }
  for(const [id,output,fmt] of [
    ["lab-aperture","lab-aperture-value",v=>v+"%"],
    ["lab-distortion","lab-distortion-value",v=>v+"%"],
    ["lab-threshold","lab-threshold-value",v=>(v/100).toFixed(2)]
  ])el(id).addEventListener("input",()=>{
    el(output).textContent=fmt(Number(el(id).value));
    draw();
  });
  el("lab-capture").addEventListener("click",()=>{
    snapshot={options:options()};splatted=false;
    el("lab-status").textContent="Observation copied into parallel sandbox; no source mutation.";
    el("lab-result").textContent="Captured projection. Double Splat may compare it to the fixed reference.";
    draw();
  });
  el("lab-splat").addEventListener("click",()=>{
    if(!snapshot){el("lab-status").textContent="Capture an observation first.";return;}
    splatted=true;
    el("lab-status").textContent="Sandbox comparison complete; candidate discrepancies remain UNRESOLVED.";
    draw();
  });
  el("lab-reset").addEventListener("click",()=>{
    snapshot=null;splatted=false;
    el("lab-status").textContent="Sandbox cleared. Sentinel lineage unchanged.";
    el("lab-result").textContent="Candidate count: unresolved · confirmed false invariants: 0 · native firing: disabled.";
    draw();
  });
  draw();
})();
