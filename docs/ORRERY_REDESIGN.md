# Orrery as a Description-Length Visualiser

The current sphere is a geometric representation. An optional Orrery view
could add an experimental visualisation of council description lengths and
typed residuals without changing the geometry contract or supervised runtime.

## Proposed view

- Plot each model's measured compressed reply length as a labelled orbit or
  radial distance from a shared, explicitly documented baseline.
- Show final-synthesis length separately from individual replies.
- Render syntactic, semantic, and epistemic residuals as distinct vector or
  layer types, with model labels and links to the underlying text.
- Display compressor name, level, byte units, and the reminder that compressed
  length is a proxy rather than formal Kolmogorov complexity.
- Preserve the existing eight-arm geometry as a separate view; do not imply
  that geometric distance is a calibrated measure of semantic agreement.

The view should be read-only and consume an in-memory council result. It should
not issue model calls, write artifacts, or alter sentinel inputs. This is an
optional future UI extension; no Orrery plotting implementation is included in
the current Python measurement and residue APIs.
