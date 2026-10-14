import { syntheticDemo, contextSeed, createController, toCSV } from "./model.js";

const $ = id => document.getElementById(id);
let demo, controller;
const show = value => { $("output").textContent = JSON.stringify(value, null, 2); };
function draw() {
  const ctx = $("view").getContext("2d"), origin = demo.model.frame.origin;
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
  try {
    demo = await syntheticDemo();
    controller = await createController(demo, await contextSeed(demo));
    draw();
    show(demo);
    for (const id of ["json", "csv", "context", "proposal"]) $(id).disabled = false;
    $("status").textContent = "Synthetic demo complete. Measured evidence, origin hash and burn receipt: unresolved. Transmission disabled.";
  } catch (error) { $("status").textContent = error.message; }
});
$("json").addEventListener("click", () => download(JSON.stringify(demo, null, 2), "scandoc-synthetic.json", "application/json"));
$("csv").addEventListener("click", () => download(toCSV(demo), "scandoc-synthetic.csv", "text/csv"));
$("context").addEventListener("click", () => show(controller.requestContext()));
$("proposal").addEventListener("click", async () => {
  try {
    const text = $("result").value;
    if (text.length > 1024*1024) throw new Error("Local proposal exceeds 1 MiB");
    show(await controller.suppliedFiringResult(JSON.parse(text)));
    $("status").textContent = "Forecast only. Observed prefix unchanged. No lifecycle authorization.";
  } catch (error) { $("status").textContent = error.message; }
});
