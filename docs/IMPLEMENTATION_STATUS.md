# Implementation status

## Implemented

- Added `src/hash1536_contract.js` and its public TypeScript declarations in
  `src/hash1536_contract.d.ts`.
- Added the additive `LAUNCH_ROLES` and `validateHash1536Readiness` exports
  from the existing `CLOUDBURNER17.js` entry point.
- Added inert validation for the six exact launch-role names, uniqueness,
  nonnegative safe-integer logical ticks, finite coordinates/measurements,
  the fixed geometry reference, unresolved qualification, and a closed gate.
- Declared the two post-launch extension types separately from launch roles.
- Kept the existing runtime, TAP/SURFACE exports, and deployment paths
  unchanged.

## Not implemented

This is not a complete invariant engine or launch implementation. It does not
assign existing eight-channel names to the six roles, define opposing pairs,
calibrate or transform geometry, compare subsystem measurements, set agreement
tolerances, issue trusted qualifications, create receipts, or perform live
actions. The two extension declarations have no runtime execution.

The previously mentioned chat readiness patch was not present in this
checkout; it was not recovered or treated as already committed.

## Source checkpoint

- Expected baseline: `f18e32ad41333c44cc53b3fc42009df3e0a0abf8`.
- Actual starting commit: `f9cbea547d8f0a867b91f8a5be254f27b46b7543`.
- The expected baseline is the starting commit's parent; the starting commit
  contains only the branch's `Initial plan` commit.
- Implementation commit verified by tests: `bbc4843` (full hash recorded in
  `agent-state.json`).
