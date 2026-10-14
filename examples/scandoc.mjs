import { syntheticDemo, toCSV, contextSeed, createController, nextProposal } from "../backend/scandoc/model.js";

const demo = await syntheticDemo();
const checkpoint = await contextSeed(demo);
const controller = await createController(demo, checkpoint);
const context = controller.requestContext();
if (process.argv.includes("--csv")) process.stdout.write(toCSV(demo));
else if (process.argv.includes("--proposal"))
  process.stdout.write(JSON.stringify(nextProposal(context.body), null, 2) + "\n");
else if (process.argv.includes("--report")) {
  const revision = process.argv[process.argv.indexOf("--revision") + 1];
  if (!/^[0-9a-f]{40}$/.test(revision)) throw new TypeError("--report requires --revision <40-char tested commit>");
  process.stdout.write(JSON.stringify({
    schema: "scandoc-synthetic-validation/2", testedRevision: revision,
    synthetic: true, evidenceKind: "local-synthetic-not-burn-or-genesis",
    cubeDigest: demo.cubeDigest, perFaceDigests: demo.perFaceDigests,
    modelDigest: demo.modelDigest, trajectoryDigest: demo.trajectoryDigest, seedDigest: context.seedHash,
    final: demo.trajectory.at(-1), centerDistanceFromRadiusOrigin: demo.centerDistanceFromRadiusOrigin,
    frequency: demo.frequency, phase: demo.phase, median: demo.median,
    sentinelSeparation: demo.sentinelSeparation, boundary: demo.boundary,
    provenance: demo.model.provenance, transmission: demo.transmission,
  }, null, 2) + "\n");
} else process.stdout.write(JSON.stringify({ ...demo, checkpoint, context,
  nextStateExample: nextProposal(context.body) }, null, 2) + "\n");
