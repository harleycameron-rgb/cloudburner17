// SCANDOC read-only exterior observer v0.1. Pure functions; no I/O, no execution adapters.
const finite = x => typeof x === 'number' && Number.isFinite(x);
export function observeExterior(events, {tolerance=1e-9}={}) {
  if (!Array.isArray(events) || !finite(tolerance) || tolerance < 0) throw new TypeError('invalid observer input');
  const seen = new Set(), anomalies = [], trace = [];
  let previous = -1;
  for (const event of events) {
    if (!event || !Number.isSafeInteger(event.sequence) || event.sequence < 0 || typeof event.eventID !== 'string' || !event.eventID) {
      anomalies.push({code:'MALFORMED_EVENT'}); continue;
    }
    if (seen.has(event.eventID)) anomalies.push({code:'DUPLICATE_ID',eventID:event.eventID});
    seen.add(event.eventID);
    if (event.sequence !== previous+1) anomalies.push({code:'SEQUENCE_GAP',eventID:event.eventID});
    previous=event.sequence;
    const p=event.position;
    if (!Array.isArray(p) || p.length!==3 || !p.every(finite)) {
      anomalies.push({code:'NONFINITE_GEOMETRY',eventID:event.eventID}); continue;
    }
    trace.push({eventID:event.eventID,sequence:event.sequence,position:[...p]});
  }
  const drift=[];
  for(let i=1;i<trace.length;i++) {
    const a=trace[i-1].position,b=trace[i].position;
    const distance=Math.hypot(...a.map((v,j)=>b[j]-v));
    if (!finite(distance)) {
      anomalies.push({code:'NONFINITE_DRIFT',from:trace[i-1].eventID,to:trace[i].eventID});
      continue;
    }
    drift.push({from:trace[i-1].eventID,to:trace[i].eventID,distance,stationary:distance<=tolerance});
  }
  return Object.freeze({schema:'scandoc-exterior-observer/0.1',nativeGate:'CLOSED',writesPermitted:false,trust:'UNVERIFIED',evidenceState:'UNKNOWN',sourceEventIDs:trace.map(x=>x.eventID),trace,drift,anomalies});
}
