import { SphericalBurnHarness } from "./src/spherical_topology.js";

<<<<<<< HEAD
/** Local diagnostic run. Caller checks are not trusted live qualifications. */
export function runSphericalBurnHarness(scenes, options = {}) {
  if (!Array.isArray(scenes) || scenes.length === 0)
    throw new TypeError("A nonempty scene array is required");
  const harness = new SphericalBurnHarness(options);
  for (const scene of scenes) {
    const module = harness.admit(scene);
    if (module.state === "burned") continue;
    const origin = harness.snapshot().sphere.origin;
    const distance = Math.hypot(...module.placement.position.map((v, i) => v-origin[i]));
    harness.converge(scene.id, scene.checks ?? [
      { name: "declared-shell-radius", ok: Math.abs(distance-module.placement.radius) < 1e-6 },
    ]);
    harness.retire(scene.id);
    harness.burn(scene.id);
  }
=======
/** Caller checks are local diagnostics, not trusted live qualifications. */
export function runSphericalBurnHarness(scenes, options = {}) {
  if (!Array.isArray(scenes) || scenes.length === 0) {
    throw new TypeError("A nonempty scene array is required");
  }

  const harness = new SphericalBurnHarness(options);

  for (const scene of scenes) {
    const module = harness.admit(scene);
    const origin = harness.snapshot().sphere.origin;
    const distance = Math.hypot(
      ...module.placement.position.map((v, i) => v-origin[i]),
    );

    harness.converge(scene.id, scene.checks ?? [{
      name: "declared-shell-radius",
      ok: Math.abs(distance-module.placement.radius) < 1e-6,
    }]);
    harness.retire(scene.id);
    harness.burn(scene.id);
  }

>>>>>>> origin/main
  return harness.snapshot();
}
