import {
  invariantTap,
  tapStream,
  runInvariantTapSession,
} from "./InvariantTap.js";
import { bridgeInvariantTapToIgnition } from "./InvariantTapBridge.js";

const PanelState = {
  events: [],
  session: null,
  bridge: null,
  safety: "UNKNOWN",
  lastHash: null,
};

export function tapSurface(eventName) {
  const tap = invariantTap(eventName);
  PanelState.events.push(eventName);
  PanelState.lastHash = tap.hash;
  return tap;
}

export function wobbleMeter() {
  if (!PanelState.session) return 0;
  const wobbleValues = PanelState.session.vector.map((event) => event.wobble);
  if (wobbleValues.length === 0) return 0;
  return wobbleValues.reduce((total, wobble) => total + wobble, 0) /
    wobbleValues.length;
}

export function hashPrinter() {
  return PanelState.lastHash || "NO_HASH_YET";
}

export function pulseGauge() {
  if (!PanelState.session) return false;
  return PanelState.session.invariantPulse;
}

export function vectorInspector() {
  if (!PanelState.session) return [];
  return PanelState.session.vector.map((event) => ({
    name: event.name,
    wobble: event.wobble,
    hash: event.hash,
    timestamp: event.timestamp,
  }));
}

export function recordSession() {
  const session = runInvariantTapSession(PanelState.events);
  const taps = tapStream(PanelState.events);
  PanelState.session = {
    ...session,
    vector: session.vector.map((event, index) => ({
      ...event,
      wobble: taps[index].wobble,
      hash: taps[index].hash,
    })),
  };
  return PanelState.session;
}

export function triggerBridge() {
  PanelState.bridge = bridgeInvariantTapToIgnition(PanelState.events);
  PanelState.safety = PanelState.bridge.invariantPulse ? "SAFE" : "HALTED";
  return PanelState.bridge;
}

export function safetyLight() {
  return PanelState.safety;
}

export function instrumentPanelSnapshot() {
  return {
    events: [...PanelState.events],
    lastHash: PanelState.lastHash,
    wobble: wobbleMeter(),
    pulse: pulseGauge(),
    vector: vectorInspector(),
    session: PanelState.session,
    bridge: PanelState.bridge,
    safety: PanelState.safety,
    status: "INVARIANT_TAP_PANEL_ACTIVE",
  };
}
