# Gate Integration Instructions

## Install

```sh
npm install cloudburner17
```

## Required Routing
All lifecycle events must pass through the stabiliser:

### Admission Gate

```js
const topo = computeTrajectory(payload, prevHash);
```

### Burn Gate

```js
const burn = burnModule(payload);
```

### Timestamp Gate

```js
const proof = verifyTimestampProof(proofObj, burn.receiptCommitment);
```

### Full Lifecycle Harness

```js
const result = await runBurnChainHarness(payload);
```

## Rules
- Do not implement custom burn semantics.
- Do not bypass the stabiliser.
- Do not redefine timestamp logic.
- Do not alter ancestry mapping.
- All repos must treat Cloudburner17 as the invariant authority.
