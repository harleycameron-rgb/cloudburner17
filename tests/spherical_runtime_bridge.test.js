import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import test from "node:test";

const bridge = fileURLToPath(
  new URL("../src/spherical_runtime_bridge.mjs", import.meta.url),
);

test("spherical runtime bridge executes dependency burns and a local dual shift", () => {
  const result = spawnSync(process.execPath, [bridge], {
    input: JSON.stringify({
      scenes: [
        { id: "root", content: "bridge-root", layer: 0 },
        { id: "arm", content: "bridge-arm", layer: 511, dependencies: ["root"] },
      ],
      shifts: [{ id: "twist", twistRadians: Math.PI / 6 }],
    }),
    encoding: "utf8",
  });
  assert.equal(result.status, 0, result.stdout + result.stderr);
  const output = JSON.parse(result.stdout);
  assert.equal(output.sourceVerified, true);
  assert.equal(output.shiftsVerified, true);
  assert.equal(output.source.events.length, 2);
  assert.deepEqual(output.source.events[1].dependencies, ["root"]);
  assert.equal(output.shiftHistory.events[0].pair.length, 2);
  assert.equal(output.shiftHistory.gateSymbol, "dual-fired-unanchored");
  assert.equal(output.shiftHistory.bitcoinAnchor, null);
  assert.equal(output.shiftHistory.signature, null);
  assert.equal(result.stdout.includes("bridge-root"), false);
  assert.equal(result.stdout.includes("bridge-arm"), false);
});

test("spherical runtime bridge rejects empty scenes before importing modules", () => {
  const result = spawnSync(
    process.execPath,
    [bridge],
    { input: JSON.stringify({ scenes: [] }), encoding: "utf8" },
  );

  assert.equal(result.status, 2);
  assert.deepEqual(JSON.parse(result.stdout), { error: "invalid_request" });
});

test("spherical runtime bridge rejects malformed JSON", () => {
  const result = spawnSync(
    process.execPath,
    [bridge],
    { input: "{", encoding: "utf8" },
  );

  assert.equal(result.status, 2);
  assert.deepEqual(JSON.parse(result.stdout), { error: "invalid_request" });
});
