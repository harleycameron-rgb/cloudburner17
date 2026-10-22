# Typed Multi-Model Residue

Typed residue keeps different forms of model disagreement distinct instead of
collapsing them into one score:

- **Syntactic** — differences in wording, formatting, or structure.
- **Semantic** — differences in meaning, claims, or interpretation.
- **Epistemic** — differences in uncertainty, evidence, or confidence.

`src/residue.py:typed_residue` accepts a sequence of mappings with exactly
`model`, `kind`, and `residual` string fields. `kind` must be one of the three
categories above. A model may contribute at most one residual of each kind;
entries are returned grouped by kind and sorted by model for deterministic
comparison. Empty residual strings are valid and represent an explicitly
empty category.

The existing `Residue(data, tag)` function and supervised residue contract are
unchanged. Typed residue is an additive research API; integrating it into the
supervised `burn → ignite → residue` output requires a separate contract change.

Example shape:

```python
typed_residue([
    {"model": "model-a", "kind": "semantic", "residual": "Different causal claim"},
    {"model": "model-b", "kind": "epistemic", "residual": "Confidence is lower"},
])
```
