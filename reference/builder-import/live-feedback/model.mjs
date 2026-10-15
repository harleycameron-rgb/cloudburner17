export const IDS = Object.freeze(['tap','surface','gain','habitat','engine','business']);
export function compute(loads, level) {
  if (!Array.isArray(loads) || loads.length !== 6 || loads.some(v => typeof v !== 'number' || !Number.isFinite(v) || v < 0 || v > 1)) throw new TypeError('Six loads in [0,1] required');
  if (typeof level !== 'number' || !Number.isFinite(level) || level < 0 || level > 1) throw new TypeError('Audio level in [0,1] required');
  const mean = loads.reduce((a,b) => a+b,0)/6;
  const variance = loads.reduce((a,b) => a+(b-mean)**2,0)/6;
  return {mean, variance, level, melt: Math.min(1, .65*(1-mean)+1.2*Math.sqrt(variance)+.35*level)};
}
export function rms(samples) {
  if (!(samples instanceof Float32Array) || !samples.length) throw new TypeError('Nonempty Float32Array required');
  let sum=0;
  for (const v of samples) { if (!Number.isFinite(v)) throw new TypeError('Nonfinite sample'); sum+=v*v; }
  return Math.min(1,Math.sqrt(sum/samples.length));
}
