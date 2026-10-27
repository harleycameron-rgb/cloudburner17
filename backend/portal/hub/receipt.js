// Content consistency only. Anyone can generate a new unsigned receipt.
const fields = ['schema', 'kind', 'separation', 'result', 'liveGate',
  'sphereWrites', 'receiptTrust', 'stored'];
export const MAX_RECEIPT_BYTES = 2 * 1024 * 1024;
const encoder = new TextEncoder();

function stable(value) {
  if (typeof value === 'number' && !Number.isFinite(value)) throw Error('Nonfinite receipt value');
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.keys(value).sort().map(key => [key, stable(value[key])]));
  }
  return value;
}
function closed(value) {
  return value && value.liveGate === 'CLOSED' && value.sphereWrites === false &&
    value.receiptTrust === 'UNVERIFIED';
}

export async function verifyReceipt(receipt) {
  if (!receipt || typeof receipt !== 'object' || Array.isArray(receipt) ||
      Object.keys(receipt).sort().join() !== [...fields, 'canonicalRecord', 'sha512'].sort().join()) {
    throw Error('Unsupported receipt envelope');
  }
  receipt = structuredClone(receipt);
  if (receipt.schema !== 'waxtablet-research-run/1' ||
      receipt.kind !== 'supplied-sample-research' || receipt.stored !== false ||
      !closed(receipt) || !closed(receipt.separation) || !closed(receipt.result)) {
    throw Error('Unexpected research gate contract');
  }
  if (typeof receipt.canonicalRecord !== 'string' ||
      encoder.encode(receipt.canonicalRecord).byteLength > MAX_RECEIPT_BYTES ||
      typeof receipt.sha512 !== 'string' || !/^[a-f0-9]{128}$/.test(receipt.sha512)) {
    throw Error('Missing or invalid integrity evidence; older receipts cannot be checked locally');
  }
  const record = JSON.parse(receipt.canonicalRecord);
  const displayed = Object.fromEntries(fields.map(key => [key, receipt[key]]));
  if (JSON.stringify(stable(record)) !== JSON.stringify(stable(displayed))) {
    throw Error('Receipt content differs from its integrity record');
  }
  if (!globalThis.crypto?.subtle) throw Error('Local integrity checking requires a secure browser context');
  const bytes = encoder.encode('waxtablet-research-run/1\0' + receipt.canonicalRecord);
  const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-512', bytes)),
    byte => byte.toString(16).padStart(2, '0')).join('');
  if (digest !== receipt.sha512) throw Error('Receipt SHA-512 mismatch');
  const samples = receipt.result.trajectory;
  if (!Array.isArray(samples) || samples.length < 2 || samples.length > 512) {
    throw Error('Invalid trajectory sample count');
  }
  let previous = -1;
  for (const sample of samples) {
    if (!Array.isArray(sample) || sample.length !== 2 ||
        !Number.isFinite(sample[0]) || sample[0] < 0 || sample[0] <= previous ||
        !Array.isArray(sample[1]) || sample[1].length !== 3 || !sample[1].every(Number.isFinite)) {
      throw Error('Invalid trajectory sample');
    }
    previous = sample[0];
  }
  // Detach from the caller's object so later mutations cannot change the
  // checked record while a caller plots or downloads it.
  return JSON.parse(JSON.stringify(receipt));
}
