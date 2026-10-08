/* ========================================================================
   CLOUD BURNER 17 — INVARIANT SLOT MACHINE MODULE (MONOLITHIC BUILD)
   Testing-Leg Runtime + Research-Leg Analytics
   © 2026 Harley Cameron — All Rights Reserved
   ======================================================================== */

import { createHash } from "crypto";

/* ========================================================================
   CORE TYPES
   ======================================================================== */

type Commitment = {
  id: string;
  admittedAt: number;
  layer: number;
  ancestry: Trajectory[];
  state: "admitted" | "retired" | "burned";
};

type Trajectory = {
  vector: any;
  time: number;
  invariantStable: boolean;
};

type BurnEvent = {
  receiptCommitment: string;
  previousEvent: string;
  originCommitment: string;
  transition: "available→burned-origin";
  gateway: "traversed";
  layer: number;
  timestamp: number;
};

type ValueExtraction = {
  origin: string;
  trajectoryWeight: number;
  longevity: number;
  scarcityBonus: number;
  extractedValue: number;
  retiredAt: number;
};

type OriginValueLedger = {
  [origin: string]: {
    burns: number;
    totalLongevity: number;
    totalTrajectoryWeight: number;
    scarcityImpact: number;
  };
};

type ScarcityModel = {
  activeCommitments: number;
  burnedCommitments: number;
  scarcityPressure: number;
};

type CloudburnerState = {
  commitments: Map<string, Commitment>;
  burns: BurnEvent[];
  originLedger: OriginValueLedger;
  scarcity: ScarcityModel;
  chainHead: string | null;
};

/* ========================================================================
   GLOBAL STATE
   ======================================================================== */

const STATE: CloudburnerState = {
  commitments: new Map(),
  burns: [],
  originLedger: {},
  scarcity: {
    activeCommitments: 0,
    burnedCommitments: 0,
    scarcityPressure: 0
  },
  chainHead: null
};

/* ========================================================================
   UTILITY — SHA-512
   ======================================================================== */

function sha512(input: string): string {
  return createHash("sha512").update(input).digest("hex");
}

/* ========================================================================
   ADMISSION — Commit module into invariant geometry
   ======================================================================== */

export function admitModule(payload: string, layer: number): Commitment {
  const id = sha512(payload + Date.now());
  const commitment: Commitment = {
    id,
    admittedAt: Date.now(),
    layer,
    ancestry: [],
    state: "admitted"
  };
  STATE.commitments.set(id, commitment);
  STATE.scarcity.activeCommitments++;
  return commitment;
}

/* ========================================================================
   CONVERGENCE — Add trajectory vector
   ======================================================================== */

export function addTrajectory(id: string, vector: any, invariantStable: boolean): void {
  const c = STATE.commitments.get(id);
  if (!c || c.state !== "admitted") return;
  c.ancestry.push({
    vector,
    time: Date.now(),
    invariantStable
  });
}

/* ========================================================================
   RETIRE — Safe execution revocation
   ======================================================================== */

export function retireModule(id: string): void {
  const c = STATE.commitments.get(id);
  if (!c || c.state !== "admitted") return;
  c.state = "retired";
}

/* ========================================================================
   BURN — Full lifecycle closure with origin preservation
   ======================================================================== */

export function burnModule(id: string): BurnEvent | null {
  const c = STATE.commitments.get(id);
  if (!c || c.state === "burned") return null;

  const origin = c.id;
  const previousEvent = STATE.chainHead || "none";

  const burn: BurnEvent = {
    receiptCommitment: c.id,
    previousEvent,
    originCommitment: origin,
    transition: "available→burned-origin",
    gateway: "traversed",
    layer: c.layer,
    timestamp: Date.now()
  };

  c.state = "burned";
  STATE.burns.push(burn);
  STATE.chainHead = burn.receiptCommitment;

  STATE.scarcity.activeCommitments--;
  STATE.scarcity.burnedCommitments++;
  STATE.scarcity.scarcityPressure =
    STATE.scarcity.burnedCommitments /
    Math.max(1, STATE.scarcity.activeCommitments);

  if (!STATE.originLedger[origin]) {
    STATE.originLedger[origin] = {
      burns: 0,
      totalLongevity: 0,
      totalTrajectoryWeight: 0,
      scarcityImpact: 0
    };
  }

  const longevity = Date.now() - c.admittedAt;
  const trajectoryWeight = c.ancestry.length;

  STATE.originLedger[origin].burns++;
  STATE.originLedger[origin].totalLongevity += longevity;
  STATE.originLedger[origin].totalTrajectoryWeight += trajectoryWeight;
  STATE.originLedger[origin].scarcityImpact += STATE.scarcity.scarcityPressure;

  return burn;
}

/* ========================================================================
   VALUE EXTRACTION — Post-burn structural dividend
   ======================================================================== */

export function extractValue(origin: string): ValueExtraction | null {
  const ledger = STATE.originLedger[origin];
  if (!ledger) return null;

  const longevity = ledger.totalLongevity;
  const trajectoryWeight = ledger.totalTrajectoryWeight;
  const scarcityBonus = ledger.scarcityImpact;

  const extractedValue =
    longevity * 0.4 +
    trajectoryWeight * 0.3 +
    scarcityBonus * 0.3;

  return {
    origin,
    trajectoryWeight,
    longevity,
    scarcityBonus,
    extractedValue,
    retiredAt: Date.now()
  };
}

/* ========================================================================
   RESEARCH LEG — Full analytics snapshot
   ======================================================================== */

export function snapshot(): any {
  return {
    chainHead: STATE.chainHead,
    commitments: Array.from(STATE.commitments.values()),
    burns: STATE.burns,
    originLedger: STATE.originLedger,
    scarcity: STATE.scarcity
  };
}

/* ========================================================================
   TESTING LEG — Invariant Slot Machine Execution
   ======================================================================== */

export function invariantSlotMachine(payload: string, layer: number): any {
  const c = admitModule(payload, layer);

  const stability = Math.random() > 0.3;
  addTrajectory(c.id, { stability }, stability);

  if (!stability) {
    const burn = burnModule(c.id);
    const value = extractValue(c.id);
    return { event: "burned", burn, value };
  }

  return { event: "survived", commitment: c };
}

/* ========================================================================
   END OF MONOLITHIC MODULE
   ======================================================================== */
