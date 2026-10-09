import {
  runSphericalBurnHarness, verifySphericalEnvelope,
} from "../CLOUDBURNER17.js";

const snapshot = runSphericalBurnHarness([
  { id: "origin-module", content: "declared origin topology", layer: 0 },
  { id: "shell-module", content: "declared shell topology", layer: 1,
    dependencies: ["origin-module"] },
]);

const expectedHead = snapshot.head;
if (!verifySphericalEnvelope(snapshot, expectedHead)) {
  throw new Error("Local spherical-envelope verification failed");
}
console.log(JSON.stringify(snapshot, null, 2));
