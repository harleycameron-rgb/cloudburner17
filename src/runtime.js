import { ingestTestResults } from "./ingest.js";

export function runtimeIgnition(results) {
  const { failed, invariantPulse, vector } = ingestTestResults(results);

  return {
    status: invariantPulse ? "IGNITION_READY" : "IGNITION_DRIFT",
    invariant: invariantPulse,
    residue: failed,
    drift: failed,
    vector,
  };
}
