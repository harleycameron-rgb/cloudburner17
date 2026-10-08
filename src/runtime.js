import { ingestTestResults } from "./ingest.js";

export function runtimeIgnition(results) {
  const { failed, invariantPulse, vector } = ingestTestResults(results);
  const invariant = failed === 0;

  return {
    status: invariant ? "IGNITION_STABLE" : "IGNITION_VARIANT",
    invariant,
    residue: failed,
    drift: failed,
    vector,
  };
}

export function canFeed(ignition) {
  return (
    ignition.invariant === true &&
    ignition.residue === 0 &&
    ignition.drift === 0 &&
    ignition.vector.length > 0
  );
}

export async function beginFeedCycle(source) {
  const batch = await source.pull();
  ingestTestResults(batch);
  const ignition = runtimeIgnition(batch);

  if (!canFeed(ignition)) {
    return {
      feed: "HALTED",
      reason: "Invariant not stable",
      ignition,
    };
  }

  return {
    feed: "ACTIVE",
    truthVector: ignition.vector,
    invariant: ignition.invariant,
    timestamp: Date.now(),
  };
}

export function harmoniseTriStream(vector) {
  const project = (pulse) =>
    vector.map(({ name, ok }) => ({ name, ok, pulse }));

  return {
    publicStudy: project("PUBLIC"),
    philosophicalReset: project("PHILOSOPHICAL"),
    businessProcedure: project("BUSINESS"),
  };
}

export function stabiliseContradiction(vector) {
  const contradictions = vector.filter((entry) => !entry.ok).length;

  return {
    contradictions,
    stabilised: contradictions > 0 ? "TENSION_HELD" : "NO_TENSION",
    field: vector,
  };
}

export function proofRhythm(vector) {
  return vector.map((entry, index) => ({
    ...entry,
    rhythmIndex: index,
    topology: index === 0 ? "ORIGIN" : "CONTINUUM",
  }));
}

export async function CLOUDBURNER17_ORCHESTRATE(source) {
  const batch = await source.pull();
  const ingestion = ingestTestResults(batch);
  const ignition = runtimeIgnition(batch);
  const feed = canFeed(ignition);

  return {
    ingestion,
    ignition,
    feedStatus: feed ? "FEED_OPEN" : "FEED_CLOSED",
    triStream: harmoniseTriStream(ignition.vector),
    contradictionField: stabiliseContradiction(ignition.vector),
    proofRhythm: proofRhythm(ignition.vector),
    organismStatus: feed ? "ALIVE" : "SLEEPING",
  };
}
