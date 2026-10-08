import { ingestTestResults } from "./ingest.js";

const MIN_INTERVAL_MS = 150;
let lastUpdate = 0;
let lastState = null;

function continuityAudit(current) {
  const now = Date.now();

  if (now - lastUpdate < MIN_INTERVAL_MS) return false;
  lastUpdate = now;

  if (!current || !Array.isArray(current.vector)) return false;
  if (lastState && current.vector.length !== lastState.vector.length) return false;
  if (current.drift !== 0) return false;

  lastState = current;
  return true;
}

export function runtimeIgnition(results) {
  const { failed, vector } = ingestTestResults(results);
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
  const batch = Array.isArray(source) ? source : await source.pull();
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

export async function safeFeed(source, orchestrate) {
  const batch = await source.pull();
  const report = await orchestrate(batch);
  const safe = continuityAudit(report?.ignition);

  return safe
    ? { status: "SAFE_UPDATE", report }
    : { status: "HALTED", reason: "Continuity violation detected" };
}

export async function continuityLoop(source, orchestrate) {
  while (true) {
    const out = await safeFeed(source, orchestrate);

    if (out.status === "HALTED") {
      console.log("SAFETY HALT:", out.reason);
      break;
    }

    console.log("SAFE PULSE:", out.report.organismStatus);
    await new Promise((resolve) => setTimeout(resolve, MIN_INTERVAL_MS));
  }
}
