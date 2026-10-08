import { ingestTestResults } from "./src/ingest.js";
import { runtimeIgnition } from "./src/runtime.js";
import { runInvariantTapSession } from "./InvariantTap.js";

export function bridgeInvariantTapToIgnition(events) {
  const tapSession = runInvariantTapSession(events);
  const results = tapSession.vector.map((event) => ({
    name: `tap-${event.name}`,
    ok: event.ok,
    timestamp: event.timestamp,
  }));
  const ingestion = ingestTestResults(results);
  const ignition = runtimeIgnition(results);

  return {
    tapSession,
    ingestion,
    ignition,
    invariantPulse: tapSession.invariantPulse && ignition.invariant,
    status: "BRIDGE_ACTIVE",
  };
}

export async function runTapBridgeCycle(source) {
  if (!source || typeof source.pull !== "function") {
    throw new TypeError("Tap source must provide a pull function");
  }

  const events = await source.pull();
  const bridge = bridgeInvariantTapToIgnition(events);

  if (!bridge.invariantPulse) {
    return {
      feed: "HALTED",
      reason: "Invariant mismatch detected",
      bridge,
    };
  }

  return {
    feed: "ACTIVE",
    bridge,
    timestamp: Date.now(),
  };
}
