# Test evidence

Recorded 2026-10-15. Runtime versions observed: Node.js `v24.21.0`, npm
`11.19.0`, Python `3.12.3`. No dependencies were added.

## Focused contract tests and coverage

Command:

```sh
node --experimental-test-coverage --test-coverage-include=src/hash1536_contract.js --test tests/hash1536_contract.test.js
```

Result: **8 passed, 0 failed**. Node's test coverage report for
`src/hash1536_contract.js` was **100.00% line, 100.00% branch, and 100.00%
function coverage**. This scope covers only the readiness validator, not the
repository's full invariant engine.

The tests check exact-role acceptance, unresolved and finite independent role
measurements, extension rejection as launch records, missing/duplicate/unknown
roles, invalid ticks, nonfinite values, unauthorized qualification, event
identity, reference, and gate constraints.

## Existing JavaScript suite

Command:

```sh
npm test
```

Result: **88 passed, 0 failed** (`node --test tests/*.test.js`). The suite was
audited before running: it makes no deployed-service or physical-control
requests. It does include existing local in-memory/simulated burn and shift
tests; these are not live actions.

## CI status check

GitHub Actions runs `38809903228` (Zero-data validation) and `38809903111`
(Backend container) both reported `action_required` and zero jobs. Failed-job
log requests returned “No failed jobs found” for each. This does not establish
a successful or failed build; no CI job logs were available.

No Python suite, type-checker, deployment, or live service was run for this
change.

## Sparse-reference repair verification

Repair commit: `9c0365a7b13957c0d6cc7d18a74c73e0612d93bf`.

Before changing the validator, the new regression tests were run against the
old implementation:

```sh
node --test tests/hash1536_contract.test.js
```

Exit code: **1**; **10 passed, 1 failed**. The sparse-geometry test failed
because the validator accepted a reference with a missing own coordinate,
including when that coordinate was inherited from a local array prototype.
This was an intentional regression demonstration.

After the fix, the focused command was:

```sh
node --experimental-test-coverage --test-coverage-include=src/hash1536_contract.js --test tests/hash1536_contract.test.js
```

Exit code: **0**; **11 passed, 0 failed**. The validator-only coverage report
was **100.00% line, 100.00% branch, and 100.00% function coverage**.

The audited existing JavaScript suite was then run:

```sh
npm test
```

Exit code: **0**; **91 passed, 0 failed**. The audit found no deployed-service
calls; existing local simulated lifecycle and subprocess tests remain part of
the suite. Runtime versions for these commands: Node.js `v24.21.0`, npm
`11.19.0`, Python `3.12.3`.

## Parallel validation

CodeQL JavaScript analysis completed with **0 alerts**. The automated code
review component reported no comments but was unavailable because its review
binary was not present; this is not an independent code-review result.
The repair was revalidated after the implementation commit: CodeQL reported
**0 JavaScript alerts**; the automated review component remained unavailable.
