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
