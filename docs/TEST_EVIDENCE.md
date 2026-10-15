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

## Parallel validation

CodeQL JavaScript analysis completed with **0 alerts**. The automated code
review component reported no comments but was unavailable because its review
binary was not present; this is not an independent code-review result.
