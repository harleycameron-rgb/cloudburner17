import {
<<<<<<< HEAD
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
=======
  runSphericalBurnHarness,
  verifySphericalEnvelope,
  SphereShiftGate,
  verifySphereShifts,
} from "../CLOUDBURNER17.js";

const source = runSphericalBurnHarness([
  { id: "origin-module", content: "declared origin topology", layer: 0 },
  {
    id: "shell-module",
    content: "declared shell topology",
    layer: 1,
    dependencies: ["origin-module"],
  },
]);

// Local self-check only. External verification needs separately trusted heads.
if (!verifySphericalEnvelope(source, source.head)) {
  throw new Error("Local spherical-envelope verification failed");
}

const gate = new SphereShiftGate(source, source.head);
gate.shift("sphere-shift-1", Math.PI / 6);
const history = gate.snapshot();

if (!verifySphereShifts(history, source.head, history.head)) {
  throw new Error("Local dual-shift verification failed");
}

console.log(JSON.stringify(history, null, 2));
>>>>>>> origin/main
