import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import test from "node:test";

const bridge = fileURLToPath(
  new URL("../src/spherical_runtime_bridge.mjs", import.meta.url),
);

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
