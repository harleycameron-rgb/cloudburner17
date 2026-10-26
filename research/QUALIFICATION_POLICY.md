# Offline six-face qualification policy (research contract)

This is a pure policy evaluator, not a source of qualification authority.

Exactly six launch faces are required: tap, surface, gain, habitat, engine, business.
Backward/forward time experiences are interfaces, not extra launch commitments.
Each face must explicitly supply semantic_state, geometry_ok, provenance_ok.
Allowed semantic values: supported, unsupported, disproven, unknown.
An advisory score (including 0.73 or 1.0) cannot turn unknown or failed predicates into supported ones.
No scores are required for acceptance.

`PolicyDecision.accepted` means **the local supplied values satisfy this toy policy only**.
A caller can fabricate inputs: the function performs NO authentication, signature
verification, trusted receipt lookup, anti-replay, transaction, geometric measurement,
or authorisation. The result must NEVER be promoted to a live firing credential.

Live gate stays CLOSED and sphere writes stay false in every output, including a
locally accepted policy result.

Run from repository root:

```sh
python -B -m unittest tests.test_qualification_contract -v
```

This isolated module is additive, does not change any deployed routes, and requires
review against existing admission and gate-writer contracts before integration.
