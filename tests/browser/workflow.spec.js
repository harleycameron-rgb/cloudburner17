import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { test, expect, controls, runDemo, canvasHasPixels } from "./fixtures.js";

// Independent of the browser model's canonicalizer and SHA-512 implementation.
function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object")
    return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${canonical(value[key])}`).join(",")}}`;
  return JSON.stringify(value);
}
const digest = value => createHash("sha512").update(canonical(value)).digest("hex");

async function download(page, id, filename) {
  const pending = page.waitForEvent("download");
  await page.locator(`#${id}`).click();
  const result = await pending;
  expect(result.suggestedFilename()).toBe(filename);
  expect(await result.failure()).toBeNull();
  return readFile(await result.path(), "utf8");
}

test.beforeEach(async ({ page }) => {
  await page.goto("/scandoc");
});

test("synthetic demo renders canvas and complete textual geometry", async ({ page }) => {
  expect(await canvasHasPixels(page)).toBe(false);
  const demo = await runDemo(page);
  expect(await canvasHasPixels(page)).toBe(true);
  await expect(page.locator("#summary")).toContainText(`Cube SHA-512: ${demo.cubeDigest}`);
  await expect(page.locator("#summary")).toContainText(`Trajectory SHA-512: ${demo.trajectoryDigest}`);
  await expect(page.locator("#summary")).toContainText("Sphere geometric radius: 0.8 diagnostic-unit");
  await expect(page.locator("#summary")).toContainText("Center distance from declared radius origin:");
  await page.getByText("Accessible textual geometry and trajectory (canvas fallback)", { exact: true }).click();
  await expect(page.locator("#geometry-data")).toBeVisible();
  const geometry = JSON.parse(await page.locator("#geometry-data").textContent());
  expect(geometry).toEqual({
    synthetic: true, frame: demo.model.frame, cubeCenter: demo.model.baseline.C,
    faces: demo.trajectory.at(-1).faces, vertices: demo.cubeState.geometry.vertices,
    sphere: demo.trajectory.at(-1).sphere, sentinel: demo.trajectory.at(-1).sentinel,
    trajectory: demo.trajectory.map(({ tick, time, sphere }) => ({ tick, time, sphere })),
  });
  expect(geometry.faces).toHaveLength(6);
  expect(geometry.vertices).toHaveLength(8);
  expect(geometry.trajectory).toHaveLength(5);
});

test("JSON and CSV downloads preserve contents, commitments and synthetic-only boundaries", async ({ page }) => {
  const shown = await runDemo(page);
  const exported = JSON.parse(await download(page, "json", "scandoc-synthetic.json"));
  expect(exported).toEqual(shown);
  expect(exported.modelDigest).toBe(digest(exported.model));
  expect(exported.cubeDigest).toBe(digest(exported.cubeState));
  expect(exported.trajectoryDigest).toBe(digest(exported.trajectory));
  expect(exported.perFaceDigests).toEqual(exported.cubeState.state.faces.map(face => digest({
    modelDigest: exported.modelDigest, frame: exported.model.frame,
    tick: exported.cubeState.state.tick, time: exported.cubeState.state.time, face,
  })));
  expect(exported.context.seedHash).toBe(digest(exported.context.body));
  expect(exported).toMatchObject({
    synthetic: true, transmission: "disabled", physicalConvergence: false, genesisReceipt: null,
    originStatus: "UNRESOLVED_NO_ORIGIN_RECEIPT",
    model: {
      policies: { transitions: "forbidden" },
      provenance: { measured: false, originHash: null, burnReceipt: null, sourceCommitIsBurnReceipt: false },
      frequency: { physical: false },
    },
    boundary: { status: "UNRESOLVED", transitionAuthorized: false, structuralMeltingAttachment: false },
    context: { authority: "read-only", transmission: "disabled", originStatus: "unresolved", receiptStatus: "unresolved" },
  });
  const csv = await download(page, "csv", "scandoc-synthetic.csv");
  const rows = csv.trimEnd().split("\n").map(line => {
    const fields = line.match(/"(?:[^"]|"")*"/g);
    expect(fields.join(",")).toBe(line);
    return fields.map(field => field.slice(1, -1).replaceAll('""', '"'));
  });
  const headers = rows.shift();
  expect(headers).toEqual(["synthetic", "tick", "time", "x", "y", "z", "geometricRadius",
    "centerDistanceFromRadiusOrigin", "vx", "vy", "vz", "sentinelSeparation", "median",
    "frequency", "frequencyUnits", "lengthUnits", "timeUnits", "cubeDigest",
    "perFaceDigests", "trajectoryDigest", "originStatus", "provenance"]);
  expect(rows).toHaveLength(exported.trajectory.length);
  rows.forEach((row, index) => {
    expect(row).toHaveLength(headers.length);
    const record = Object.fromEntries(headers.map((key, i) => [key, row[i]]));
    const state = exported.trajectory[index];
    expect(record).toMatchObject({
      synthetic: "true", tick: String(state.tick), time: String(state.time),
      geometricRadius: String(state.sphere.radius),
      cubeDigest: exported.cubeDigest, trajectoryDigest: exported.trajectoryDigest,
      perFaceDigests: exported.perFaceDigests.join(";"), originStatus: exported.originStatus,
      frequency: String(exported.frequency.value), frequencyUnits: "cycles/synthetic-second",
      lengthUnits: state.frame.units.length, timeUnits: state.frame.units.time,
    });
    expect(["x", "y", "z"].map(key => Number(record[key]))).toEqual(state.sphere.center);
    expect(["vx", "vy", "vz"].map(key => Number(record[key]))).toEqual(state.sphere.velocity);
    expect(Number(record.centerDistanceFromRadiusOrigin)).toBeCloseTo(
      Math.hypot(...state.sphere.center.map((v, i) => v - exported.model.frame.origin[i])), 12);
    expect(Number(record.sentinelSeparation)).toBeCloseTo(
      Math.hypot(...state.sphere.center.map((v, i) => v - state.sentinel[i])), 12);
    expect(JSON.parse(record.provenance)).toEqual(exported.model.provenance);
  });
});

test("exact next-state example is accepted only as an unverified forecast", async ({ page }) => {
  const demo = await runDemo(page);
  const summary = await page.locator("#summary").textContent();
  const geometry = await page.locator("#geometry-data").textContent();
  await page.locator("#context").click();
  expect(JSON.parse(await page.locator("#output").textContent())).toEqual(demo.context);
  await page.locator("#example").click();
  await expect(page.locator("#status")).toContainText("NOT submitted");
  expect(JSON.parse(await page.locator("#output").textContent())).toEqual(demo.context);
  const example = JSON.parse(await page.locator("#result").inputValue());
  expect(example.body).toEqual(demo.context.body);
  expect(example.proposals).toHaveLength(1);
  expect(example.proposals[0]).toMatchObject({
    tick: 5, time: 5, sphere: { radius: 0.75, center: [1025.5, 1024, 0], velocity: [-0.1, 0, 0] },
  });
  await page.locator("#proposal").click();
  await expect(page.locator("#status")).toHaveText(
    "Forecast only. Observed prefix unchanged. No lifecycle authorization.");
  const forecast = JSON.parse(await page.locator("#output").textContent());
  expect(forecast).toMatchObject({
    stream: "forecast", status: "unverified-proposal", geometryAcceptance: "ACCEPTED",
    policyStatus: "ACCEPTED", physicalEvidence: "UNRESOLVED", transitionAuthorized: false,
    observedDigest: demo.trajectoryDigest, states: example.proposals,
    boundary: { status: "UNRESOLVED", transitionAuthorized: false, structuralMeltingAttachment: false },
  });
  expect(forecast.boundary.unresolved.length).toBeGreaterThan(0);
  await expect(page.locator("#summary")).toHaveText(summary);
  await expect(page.locator("#geometry-data")).toHaveText(geometry);
  expect(JSON.parse(await download(page, "json", "scandoc-synthetic.json"))).toEqual(demo);
});

for (const scenario of ["policy-invalid", "malformed JSON", "invalid schema"]) {
  test(`${scenario} rejection invalidates stale state and rerun recovers`, async ({ page }) => {
    const demo = await runDemo(page);
    await page.locator("#example").click();
    const example = JSON.parse(await page.locator("#result").inputValue());
    let input;
    if (scenario === "policy-invalid") {
      example.proposals[0].sphere.radius = 0.76; // Positive finite geometry, wrong committed linear policy.
      input = JSON.stringify(example);
    } else if (scenario === "invalid schema") {
      input = JSON.stringify({ ...example, identity: "extra" });
    } else {
      input = '{"body":';
    }
    await page.locator("#result").fill(input);
    await page.locator("#proposal").click();
    const code = scenario === "policy-invalid" ? "POLICY_REJECTION" : "INVALID_INPUT";
    await expect(page.locator("#status")).toContainText(code);
    await expect(page.locator("#status")).toContainText("STALE; rerun the local demo");
    if (scenario === "policy-invalid")
      await expect(page.locator("#status")).toContainText("Forecast violates committed linear-next/1 source policy");
    await expect(page.locator("#status")).toHaveAttribute("aria-busy", "false");
    for (const id of controls) await expect(page.locator(`#${id}`)).toBeDisabled();
    await expect(page.locator("#summary")).toHaveText("STALE — no current export or proposal context.");
    await expect(page.locator("#geometry-data")).toHaveText("STALE — geometry from the prior run is not current.");
    await expect(page.locator("#output")).toContainText("STALE —");
    await expect(page.locator("#result")).toHaveValue("");
    expect(await canvasHasPixels(page), "Stale geometry must not remain painted").toBe(false);
    await expect(page.locator("#demo")).toBeEnabled();
    expect(await runDemo(page)).toEqual(demo);
    expect(await canvasHasPixels(page)).toBe(true);
    await expect(page.locator("#summary")).not.toContainText("STALE");
    await page.locator("#example").click();
    await page.locator("#proposal").click();
    await expect(page.locator("#status")).toContainText("Forecast only.");
  });
}
