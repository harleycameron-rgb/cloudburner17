# Multi-LLM invariant admission contract

`src/admission.py` implements the candidate-level admission checks and linked
torsion commitment for the invariant engine. It is an in-memory, dependency-free
API and does not replace the existing supervised execution pipeline.

## Admission

Create an `AdmissionCandidate` for each agent. Each candidate supplies:

- `transform(state)`: its state action `L_g`.
- `preserves_curvature`: confirmation that its action belongs to the
  curvature-preserving group on the domain being admitted.
- `preserves_topology_flow(state)`: verifies manifold and flow continuity for
  each transformed cycle state. The live submission API compares the supplied
  before/after manifold and flow snapshots.
- `observe(transformed_state)`: whether the transformed massless state was
  observed.
- `curvature_continuous(transformed_state)`: whether curvature is continuous
  on a neighbourhood of that state.

States are mappings. Both cycle states and massless states contain finite real
`kappa` and `rho` values; cycle states additionally contain finite `kappa_p`
and `kappa_s`. Massless input states must have `kappa == rho == 0`.
`evaluate_admission(candidates, cycle, massless_states)` returns one
`AdmissionResult` per candidate, including each checked predicate and the
admission decision. The false-invariant count is the number of transformed
cycle states where `kappa_p != kappa_s`. Curvature drift is the sum of absolute
curvature changes over the cycle. Residue score is the sum of absolute
transformed residues; residue minimization is evaluated against the supplied
candidate set. A candidate is admitted only if it passes every contract
predicate, has zero cycle drift, and attains the minimum residue score.

Curvature preservation remains an explicit domain-level candidate attestation.
Topology/flow preservation is a callback evaluated for each transformed cycle
state; the live submission API verifies equality of manifold and flow snapshots.
These finite checks do not establish domain-wide properties beyond the supplied
states. The engine independently checks massless-state preservation and cycle
drift. Observation and local curvature continuity are candidate callbacks.

## Torsion commitment

`commit_torsion(previous_hash, geometric_state, derive_components, modulus)`
calls `derive_components` with the underlying geometric state and expects three
integer curvature components. It computes their sum modulo `modulus`, encodes
the result as a fixed-width unsigned big-endian integer, and returns the
torsion and lowercase SHA-256 digest of `previous_hash_bytes || encoded_torsion`.
The previous hash must be a 32-byte digest (or its 64-character hexadecimal
representation). Components are never derived from the previous hash.

## Specification mapping

- Curvature-preserving action and topology/flow preservation: candidate fields
  `preserves_curvature` and `preserves_topology_flow`.
- Massless set, observation, and preservation: zero-valued `kappa`/`rho` input
  states and the `observe` callback.
- Torsion combiner and hash chain: `commit_torsion`.
- False-invariant count: `AdmissionResult.false_invariant_count`.
- Life valuation: `curvature_continuous`, massless preservation, zero cycle
  drift, and candidate-set residue minimization.
- Final admission: `AdmissionResult.admitted`.

Run the existing tests with:

```sh
PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tests -v
```
