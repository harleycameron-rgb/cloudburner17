import { createHash } from "node:crypto";
import {
  sphericalGeometry, radialPlacement, verifySphericalEnvelope,
} from "./spherical_topology.js";

const copy = value => structuredClone(value);

const canonical = value => {
  if (Array.isArray(value)) return "["+value.map(canonical).join(",")+"]";
  if (value && typeof value === "object") {
    return "{"+Object.keys(value).sort().map(k =>
      JSON.stringify(k)+":"+canonical(value[k])).join(",")+"}";
  }
  if (typeof value === "number" && !Number.isFinite(value)) {
    throw new TypeError("Nonfinite value");
  }
  if (value === undefined) throw new TypeError("Undefined value");
  return JSON.stringify(value);
};

const hash = value =>
  createHash("sha512").update(canonical(value)).digest("hex");
const HEX = /^[0-9a-f]{128}$/;

function project(snapshot, geometry) {
  return snapshot.events.map(event => ({
    id: event.id,
    sourceEnvelope: event.envelopeHash,
    topologyHash: event.topologyHash,
    placement: radialPlacement(
      geometry, event.topologyHash, event.lifecycle.layer,
    ),
  }));
}

function pairFor(segment, surface) {
  const segmentHash = hash(segment);

  return [
    {
      schema: "sphere-shift-firing/1",
      kind: "surface-projection",
      segmentHash,
      geometryHash: hash(segment.toGeometry),
      projectionHash: hash(surface),
    },
    {
      schema: "sphere-shift-firing/1",
      kind: "linear-checkpoint",
      segmentHash,
      sourceHead: segment.sourceHead,
      sourceGenesis: segment.sourceGenesis,
      timestampState: "not-submitted",
      bitcoinAnchor: null,
    },
  ];
}

/** Atomic means a synchronous memory commit, not a physical experiment. */
export class SphereShiftGate {
  #source;
  #geometry;
  #head;
  #events = [];

  constructor(sourceSnapshot, trustedSourceHead) {
    if (!verifySphericalEnvelope(sourceSnapshot, trustedSourceHead)) {
      throw new Error(
        "Verified source envelope and independently trusted head required",
      );
    }

    this.#source = copy(sourceSnapshot);
    this.#geometry = copy(sourceSnapshot.sphere);
    this.#head = hash({
      schema: "sphere-shift-genesis/1",
      sourceHead: trustedSourceHead,
      sourceGenesis: sourceSnapshot.genesis,
      geometry: this.#geometry,
    });
  }

  shift(segmentId, twistRadians) {
    if (typeof segmentId !== "string" || !segmentId.length ||
        !Number.isFinite(twistRadians)) {
      throw new TypeError("Invalid shift segment");
    }

    const retry = this.#events.find(e => e.segment.id === segmentId);

    if (retry) {
      if (retry.segment.twistRadians !== twistRadians) {
        throw new Error("Changed shift retry rejected");
      }
      return copy(retry);
    }

    if (!this.#source.events.length) {
      throw new Error("No burned trajectory to project");
    }

    const toGeometry = sphericalGeometry({
      origin: this.#geometry.origin,
      axis: this.#geometry.axis,
      tilt: this.#geometry.tilt+twistRadians,
      radius: this.#geometry.radius,
      layerSpacing: this.#geometry.layerSpacing,
    });

    const surface = project(this.#source, toGeometry);
    const segment = {
      schema: "sphere-shift-segment/1",
      id: segmentId,
      sequence: this.#events.length,
      previousShift: this.#head,
      sourceHead: this.#source.head,
      sourceGenesis: this.#source.genesis,
      fromGeometry: copy(this.#geometry),
      toGeometry,
      twistRadians,
    };

    const event = {
      schema: "sphere-dual-shift/1",
      segment,
      pair: pairFor(segment, surface),
      surface,
      atomicity: "single-synchronous-memory-commit",
      gateSymbol: "dual-fired-unanchored",
      atomicGas: {
        geometry: "separate-conceptual-origin",
        evidence: "unverified",
      },
    };

    event.eventHash = hash(event);

    // Prepare the complete pair before changing internal state.
    this.#events.push(event);
    this.#geometry = toGeometry;
    this.#head = event.eventHash;

    return copy(event);
  }

  snapshot() {
    return copy({
      schema: "sphere-shift-history/1",
      source: this.#source,
      geometry: this.#geometry,
      events: this.#events,
      head: this.#head,
      gateSymbol: this.#events.length
        ? "dual-fired-unanchored" : "sphere-ready",
      signature: null,
      bitcoinAnchor: null,
    });
  }
}

export function verifySphereShifts(
  history, trustedSourceHead, expectedShiftHead,
) {
  try {
    if (history.schema !== "sphere-shift-history/1" ||
        !HEX.test(expectedShiftHead) ||
        history.signature !== null ||
        history.bitcoinAnchor !== null ||
        !verifySphericalEnvelope(history.source, trustedSourceHead)) {
      return false;
    }

    let geometry = history.source.sphere;
    let head = hash({
      schema: "sphere-shift-genesis/1",
      sourceHead: trustedSourceHead,
      sourceGenesis: history.source.genesis,
      geometry,
    });

    const ids = new Set();

    for (const [sequence, event] of history.events.entries()) {
      const { eventHash, ...body } = event;
      const s = event.segment;

      const target = sphericalGeometry({
        origin: geometry.origin,
        axis: geometry.axis,
        tilt: geometry.tilt+s.twistRadians,
        radius: geometry.radius,
        layerSpacing: geometry.layerSpacing,
      });
      const surface = project(history.source, target);

      if (event.schema !== "sphere-dual-shift/1" ||
          s.schema !== "sphere-shift-segment/1" ||
          typeof s.id !== "string" || !s.id.length || ids.has(s.id) ||
          !Number.isFinite(s.twistRadians) ||
          s.sequence !== sequence ||
          s.previousShift !== head ||
          s.sourceHead !== trustedSourceHead ||
          s.sourceGenesis !== history.source.genesis ||
          canonical(s.fromGeometry) !== canonical(geometry) ||
          canonical(s.toGeometry) !== canonical(target) ||
          canonical(event.surface) !== canonical(surface) ||
          canonical(event.pair) !== canonical(pairFor(s, surface)) ||
          event.atomicity !== "single-synchronous-memory-commit" ||
          event.gateSymbol !== "dual-fired-unanchored" ||
          canonical(event.atomicGas) !== canonical({
            geometry: "separate-conceptual-origin",
            evidence: "unverified",
          }) ||
          hash(body) !== eventHash) {
        return false;
      }

      ids.add(s.id);
      geometry = target;
      head = eventHash;
    }

    return head === expectedShiftHead && head === history.head &&
      canonical(history.geometry) === canonical(geometry) &&
      history.gateSymbol === (
        history.events.length ? "dual-fired-unanchored" : "sphere-ready"
      );
  } catch {
    return false;
  }
}

/** Rendering state only; not a qualification or security indicator. */
export function gateSymbolSVG(state = "sphere-ready") {
  if (!["sphere-ready", "dual-fired-unanchored"].includes(state)) {
    throw new TypeError("Unknown gate symbol state");
  }

  const fired = state === "dual-fired-unanchored";
  const color = fired ? "#ffb347" : "#4fd8ff";

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" role="img">
<title>${fired ? "Dual firing; Bitcoin timestamp unsubmitted" : "Sphere shift ready"}</title>
<rect width="256" height="256" rx="16" fill="#050a14"/>
<circle cx="128" cy="128" r="88" fill="none" stroke="#4fd8ff" stroke-width="2"/>
<ellipse cx="128" cy="128" rx="42" ry="88" fill="none" stroke="#4fd8ff" stroke-width="2" transform="rotate(30 128 128)"/>
<path d="M40 128H216M128 40V216" fill="none" stroke="#4fd8ff" stroke-width="1"/>
<path d="M66 190Q128 222 190 190" fill="none" stroke="${color}" stroke-width="3" stroke-dasharray="5 5"/>
<circle cx="84" cy="103" r="8" fill="${color}"/>
<circle cx="172" cy="153" r="8" fill="${color}"/>
<path d="M84 103L128 128L172 153" fill="none" stroke="${color}" stroke-width="3"/>
<circle cx="128" cy="128" r="5" fill="#ffffff"/>
<text x="128" y="235" text-anchor="middle" fill="#ffffff" font-size="10" font-family="monospace">${fired ? "DUAL / UNANCHORED" : "SPHERE / READY"}</text>
</svg>`;
}
