import { createHash, randomUUID } from "node:crypto";
import {
  admitModule, participateInConvergence, retireModule, burnModule,
} from "./burn_lifecycle.js";

export const SHARED_ORIGIN = Object.freeze([1024, 1024, 0]);

const HEX = /^[0-9a-f]{128}$/;
const copy = value => structuredClone(value);
const sha512 = value => createHash("sha512").update(value).digest("hex");

function canonical(value) {
  if (Array.isArray(value)) return "[" + value.map(canonical).join(",") + "]";
  if (value && typeof value === "object") {
    return "{" + Object.keys(value).sort().map(
      key => JSON.stringify(key) + ":" + canonical(value[key]),
    ).join(",") + "}";
  }
  if (typeof value === "number" && !Number.isFinite(value)) {
    throw new TypeError("Non-finite canonical value");
  }
  if (value === undefined) throw new TypeError("Undefined canonical value");
  return JSON.stringify(value);
}

const digest = value => sha512(canonical(value));
const cross = (a, b) => [
  a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0],
];

function unit(vector) {
  if (!Array.isArray(vector) || vector.length !== 3 ||
      vector.some(v => !Number.isFinite(v))) throw new TypeError("Invalid axis");
  const norm = Math.hypot(...vector);
  if (!Number.isFinite(norm) || norm === 0) throw new TypeError("Invalid axis norm");
  return vector.map(v => v / norm);
}

export function sphericalGeometry({
  origin = SHARED_ORIGIN, axis = [0, 0, 1], tilt = Math.PI / 6,
  radius = 1, layerSpacing = 1,
} = {}) {
  if (!Array.isArray(origin) || origin.length !== 3 ||
      Array.from(origin).some(v => !Number.isFinite(v) || Math.abs(v) > 1e9) ||
      !Number.isFinite(tilt) || !Number.isFinite(radius) || radius <= 0 ||
      radius > 1e6 || !Number.isFinite(layerSpacing) ||
      layerSpacing <= 0 || layerSpacing > 1e6) throw new TypeError("Invalid sphere");
  const n = unit(axis);
  const reference = Math.abs(n[2]) < 0.9 ? [0, 0, 1] : [0, 1, 0];
  const u = unit(cross(reference, n));
  // Rotate the pole toward u; this is an orientation, not a physical polar force.
  const pole = unit(n.map((v, i) => Math.cos(tilt)*v + Math.sin(tilt)*u[i]));
  const v = unit(cross(pole, u));
  const tangent = unit(cross(v, pole));
  return {
    schema: "invariant-sphere/1", origin: [...origin], axis: n,
    shiftedAxis: pole, basis: [tangent, v, pole], tilt, radius, layerSpacing,
    layers: 512, aperture: "declared-receiving-band",
  };
}

export function radialPlacement(geometry, topologyHash, layer) {
  if (!HEX.test(topologyHash) || !Number.isInteger(layer) || layer < 0 || layer >= 512)
    throw new TypeError("Placement requires a SHA-512 hash and layer 0..511");
  const phi = 2*Math.PI * (parseInt(topologyHash.slice(0, 12), 16) / 2**48);
  const z = 2*(parseInt(topologyHash.slice(12, 24), 16) / 2**48)-1;
  const sine = Math.sqrt(Math.max(0, 1-z*z));
  const local = [sine*Math.cos(phi), sine*Math.sin(phi), z];
  const direction = [0, 1, 2].map(i =>
    local.reduce((sum, component, j) => sum + component*geometry.basis[j][i], 0));
  const radius = geometry.radius + layer*geometry.layerSpacing;
  return { layer, radius, direction,
    position: geometry.origin.map((o, i) => o + radius*direction[i]),
    longitude: phi, colatitude: Math.acos(z) };
}

/** In-memory diagnostic lifecycle adapter. No keys, network or external anchors. */
export class SphericalBurnHarness {
  #sphere;
  #runId;
  #genesis;
  #head;
  #lifecycleHead = "none";
  #modules = new Map();
  #events = [];

  constructor(options = {}) {
    this.#sphere = sphericalGeometry(options);
    // Namespace receipts so separate sessions cannot overwrite native commitments.
    this.#runId = randomUUID();
    this.#genesis = digest({
      schema: "spherical-genesis/1", runId: this.#runId, sphere: this.#sphere,
    });
    this.#head = this.#genesis;
  }

  admit({ id, content, layer = 0, dependencies = [] }) {
    if (typeof id !== "string" || !id.length ||
        typeof content !== "string" || !content.length ||
        !Number.isInteger(layer) || layer < 0 || layer >= 512 ||
        !Array.isArray(dependencies) ||
        Array.from(dependencies).some(d => typeof d !== "string") ||
        new Set(dependencies).size !== dependencies.length) {
      throw new TypeError("Invalid spherical admission");
    }
    const topologyHash = digest({
      id, content, layer, dependencies, sphere: this.#sphere,
    });
    const existing = this.#modules.get(id);
    if (existing) {
      if (existing.topologyHash !== topologyHash)
        throw new Error("Changed-content retry rejected");
      return this.#view(existing);
    }
    if (dependencies.some(d => !this.#modules.has(d)))
      throw new Error("Dependencies must already be admitted");
    const commitment = digest({
      topologyHash, runId: this.#runId, genesis: this.#genesis,
    });
    const module = admitModule(commitment, layer);
    const record = {
      id, topologyHash, commitment, dependencies: [...dependencies], module,
      placement: radialPlacement(this.#sphere, topologyHash, layer),
      converged: false, burn: null,
    };
    this.#modules.set(id, record);
    return this.#view(record);
  }

  #get(id) {
    const record = this.#modules.get(id);
    if (!record) throw new Error("Unknown module");
    return record;
  }

  #view(record) {
    return copy({
      id: record.id, topologyHash: record.topologyHash,
      commitment: record.commitment, dependencies: record.dependencies,
      state: record.module.state, converged: record.converged,
      placement: record.placement,
    });
  }

  converge(id, vector) {
    const record = this.#get(id);
    if (!Array.isArray(vector) || !vector.length || Array.from(vector).some(e =>
      !e || typeof e.name !== "string" || !e.name.length || typeof e.ok !== "boolean")) {
      throw new TypeError("Convergence requires nonempty named boolean checks");
    }
    const normalized = vector.map(e => ({ invariant: e.ok, name: e.name }));
    record.converged = participateInConvergence(record.module, normalized) === "ok";
    return this.#view(record);
  }

  retire(id) {
    const record = this.#get(id);
    if (!record.converged) throw new Error("Retirement requires passing convergence");
    if (record.dependencies.some(d => this.#get(d).module.state !== "burned"))
      throw new Error("Retirement requires burned dependencies");
    // Native ancestry records this module's convergence, not cross-module burns.
    // The dependency burn-order gate above is enforced separately by this adapter.
    retireModule(record.module, [record.module.moduleId]);
    return this.#view(record);
  }

  burn(id) {
    const record = this.#get(id);
    if (record.burn) return copy(record.burn);
    if (record.module.state !== "retired") throw new Error("Burn requires retirement");
    const { burnEvent, newChainHead } = burnModule(record.module, this.#lifecycleHead);
    const event = {
      schema: "spherical-burn/1", sequence: this.#events.length,
      previousEnvelope: this.#head, genesis: this.#genesis,
      id: record.id, topologyHash: record.topologyHash,
      dependencies: [...record.dependencies], placement: copy(record.placement),
      lifecycle: burnEvent, lifecycleHash: newChainHead,
      pulse: { kind: "radial-burn", origin: [...this.#sphere.origin],
               radius: record.placement.radius },
    };
    event.envelopeHash = digest(event);
    this.#lifecycleHead = newChainHead;
    this.#head = event.envelopeHash;
    this.#events.push(event);
    record.burn = event;
    return copy(event);
  }

  snapshot() {
    return copy({
      schema: "spherical-continuity/1", runId: this.#runId,
      sphere: this.#sphere, genesis: this.#genesis, head: this.#head,
      lifecycleHead: this.#lifecycleHead,
      modules: [...this.#modules.values()].map(r => this.#view(r)),
      events: this.#events, signature: null, bitcoinAnchor: null,
      mode: "spherical-projection",
    });
  }
}

/** Checks integrity of the exported burned-event envelope, not author identity. */
export function verifySphericalEnvelope(snapshot, expectedHead) {
  try {
    if (!snapshot || snapshot.schema !== "spherical-continuity/1" ||
        !HEX.test(expectedHead) || snapshot.signature !== null ||
        snapshot.bitcoinAnchor !== null || !Array.isArray(snapshot.events)) return false;
    const sphere = snapshot.sphere;
    const rebuilt = sphericalGeometry({
      origin: sphere.origin, axis: sphere.axis, tilt: sphere.tilt,
      radius: sphere.radius, layerSpacing: sphere.layerSpacing,
    });
    // Recompute the orientation; the declaration is also bound by genesis.
    if (sphere.schema !== rebuilt.schema || sphere.layers !== 512 ||
        sphere.aperture !== rebuilt.aperture ||
        !Array.isArray(sphere.shiftedAxis) || sphere.shiftedAxis.length !== 3 ||
        sphere.shiftedAxis.some((v, i) => !Number.isFinite(v) ||
          Math.abs(v-rebuilt.shiftedAxis[i]) > 1e-12) ||
        !Array.isArray(sphere.basis) || sphere.basis.length !== 3 ||
        sphere.basis.some((v, i) => !Array.isArray(v) || v.length !== 3 ||
          v.some((x, j) => !Number.isFinite(x) ||
            Math.abs(x-rebuilt.basis[i][j]) > 1e-12)) ||
        sphere.basis.some(v => unit(v).some((x, i) => Math.abs(x-v[i]) > 1e-10)) ||
        sphere.basis.some((a, i) => sphere.basis.some((b, j) =>
          i !== j && Math.abs(a.reduce((s, v, k) => s+v*b[k], 0)) > 1e-10))) return false;
    let head = digest({
      schema: "spherical-genesis/1", runId: snapshot.runId, sphere,
    });
    if (head !== snapshot.genesis) return false;
    let lifecycleHead = "none";
    const burned = new Set();
    const commitments = new Set();
    for (const [sequence, event] of snapshot.events.entries()) {
      const { envelopeHash, ...body } = event;
      const lifecycle = event.lifecycle;
      if (event.schema !== "spherical-burn/1" || event.sequence !== sequence ||
          event.previousEnvelope !== head || event.genesis !== snapshot.genesis ||
          burned.has(event.id) || !Array.isArray(event.dependencies) ||
          event.dependencies.some(id => !burned.has(id)) ||
          !HEX.test(event.topologyHash) ||
          lifecycle.previousEvent !== lifecycleHead ||
          lifecycle.transition !== "available→burned-origin" ||
          lifecycle.gateway !== "traversed" || !Number.isFinite(lifecycle.timestamp) ||
          commitments.has(lifecycle.receiptCommitment) ||
          lifecycle.receiptCommitment !== digest({
            topologyHash: event.topologyHash, runId: snapshot.runId, genesis: snapshot.genesis,
          }) ||
          lifecycle.originCommitment !== sha512(lifecycle.receiptCommitment+"::origin") ||
          digest(body) !== envelopeHash ||
          sha512(JSON.stringify(lifecycle)) !== event.lifecycleHash ||
          canonical(event.placement) !== canonical(
            radialPlacement(sphere, event.topologyHash, lifecycle.layer)) ||
          canonical(event.pulse) !== canonical({
            kind: "radial-burn", origin: sphere.origin, radius: event.placement.radius,
          })) return false;
      burned.add(event.id);
      commitments.add(lifecycle.receiptCommitment);
      head = envelopeHash;
      lifecycleHead = event.lifecycleHash;
    }
    return head === snapshot.head && head === expectedHead &&
      lifecycleHead === snapshot.lifecycleHead;
  } catch {
    return false;
  }
}
