# Multi-LLM invariant admission contract

`src/admission.py` implements the candidate-level admission checks and linked
torsion commitment for the invariant engine. It is an in-memory, dependency-free
API and does not replace the existing supervised execution pipeline.

## Admission

Create an `AdmissionCandidate` for each agent. Each candidate supplies:

- `transform(state)`: its state action `L_g`.
- `preserves_curvature`: confirmation that its action belongs to the
  curvature-preserving group on the domain being admitted.
- `preserves_topology_flow`: confirmation that it preserves `τ(M)` and its
  flow structure.
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

The domain-wide curvature and topology/flow preservation fields are explicit
candidate attestations because these properties cannot be inferred from a
finite sample. The engine independently checks massless-state preservation and
cycle drift on the supplied states. Observation and local continuity are also
candidate callbacks so callers can apply the semantics of their state space.

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

## Runtime ignition

`src/runtime_ignition.py` provides `run_runtime_ignition(candidates, cycle,
assets, derive_components, candidate_name=None)`. `RuntimeAssets` carries the
already-loaded topology map, curvature/flow contract, zero residue state,
non-empty massless state sequence, torsion modulus, and SHA-256 genesis hash.
The function checks these in-memory values, ignites the six zero-state stubs,
then applies the existing admission and torsion APIs. It returns a `LIVE` result
with runtime topology/massless seals and the per-cycle torsion/hash chain, or
raises `RuntimeIgnitionError` on a failed ignition contract.

This API performs no filesystem access. Any host-side asset loading must occur
before the zero-data guard is installed; passing a path is not supported.
Runtime ignition additionally requires the admitted candidate's cycle residue
score to be zero, as required by the live-engine contract.

Run the existing tests with:

```sh
PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tests -v
```
