const MAX_INPUT_BYTES = 1024 * 1024;
const MAX_SCENES = 512;
const MAX_SHIFTS = 512;

async function readRequest() {
  const chunks = [];
  let size = 0;

  for await (const chunk of process.stdin) {
    size += chunk.length;
    if (size > MAX_INPUT_BYTES) {
      throw new TypeError("Request exceeds the 1 MiB limit");
    }
    chunks.push(chunk);
  }

  let request;
  try {
    request = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  } catch {
    throw new TypeError("Request must be valid JSON");
  }
  if (!request || typeof request !== "object" || Array.isArray(request)) {
    throw new TypeError("Request must be an object");
  }
  if (!Array.isArray(request.scenes) ||
      request.scenes.length === 0 ||
      request.scenes.length > MAX_SCENES) {
    throw new TypeError("scenes must contain between 1 and 512 entries");
  }

  const options = request.options ?? {};
  if (!options || typeof options !== "object" || Array.isArray(options)) {
    throw new TypeError("options must be an object");
  }

  const shifts = request.shifts ?? [];
  if (!Array.isArray(shifts) || shifts.length > MAX_SHIFTS ||
      shifts.some(shift => !shift || typeof shift !== "object" ||
        Array.isArray(shift) || typeof shift.id !== "string" ||
        !Number.isFinite(shift.twistRadians))) {
    throw new TypeError("shifts must contain valid id and twistRadians entries");
  }

  return { scenes: request.scenes, options, shifts };
}

async function run() {
  const { scenes, options, shifts } = await readRequest();
  const { SphericalBurnHarness, verifySphericalEnvelope } =
    await import("./spherical_topology.js");

  const harness = new SphericalBurnHarness(options);
  for (const scene of scenes) {
    const module = harness.admit(scene);
    const origin = harness.snapshot().sphere.origin;
    const distance = Math.hypot(
      ...module.placement.position.map((value, index) => value - origin[index]),
    );
    const checks = scene.checks ?? [{
      name: "declared-shell-radius",
      ok: Math.abs(distance - module.placement.radius) < 1e-6,
    }];

    harness.converge(scene.id, checks);
    harness.retire(scene.id);
    harness.burn(scene.id);
  }

  const source = harness.snapshot();
  if (!verifySphericalEnvelope(source, source.head)) {
    throw new Error("Spherical envelope verification failed");
  }

  let shiftHistory = null;
  let shiftsVerified = null;
  if (shifts.length) {
    const { SphereShiftGate, verifySphereShifts } =
      await import("./sphere_shift_gate.js");
    const gate = new SphereShiftGate(source, source.head);
    for (const shift of shifts) {
      gate.shift(shift.id, shift.twistRadians);
    }
    shiftHistory = gate.snapshot();
    shiftsVerified = verifySphereShifts(
      shiftHistory,
      source.head,
      shiftHistory.head,
    );
    if (!shiftsVerified) {
      throw new Error("Spherical shift verification failed");
    }
  }

  return {
    status: "ok",
    source,
    sourceVerified: true,
    shiftHistory,
    shiftsVerified,
    trust: "local verification only; no external signature or Bitcoin anchor",
  };
}

try {
  const result = await run();
  process.stdout.write(JSON.stringify(result));
} catch (error) {
  const code = error instanceof TypeError ? "invalid_request" :
    error?.code === "ERR_MODULE_NOT_FOUND" ? "runtime_unavailable" :
      "spherical_runtime_failed";
  process.stdout.write(JSON.stringify({ error: code }));
  process.exitCode = code === "invalid_request" ? 2 :
    code === "runtime_unavailable" ? 3 : 1;
}
