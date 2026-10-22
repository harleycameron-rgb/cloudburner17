# MDL Convergence Test

This framework compares independent model answers using minimum-description-
length (MDL) ideas. It is an empirical diagnostic, not a proof that a
conclusion is true or that the system has found a shortest program.

## Current measurement

`src/multi_llm_council_k.py` records UTF-8 byte length and zlib level-9
compressed byte length for each council reply and the final synthesis. The
profile is included in `CouncilResult` before its canonical SHA-512 sentinel is
computed, so changing an answer or its measured length changes the sentinel.
Measurements are performed in memory and make no additional model or
filesystem calls.

Compressed length is a compressor-dependent description-length proxy. It is
not a formal Kolmogorov-complexity upper bound: a strict bound would also need
to account for the decoder/program and encoding conventions. Results from
different compressor implementations or versions should not be compared
without recording those details.

## Convergence protocol

1. Fix the topic, model set, prompt template, and output budget before a run.
2. Preserve each independent answer and the synthesis as separate artifacts.
3. Compare answer agreement and typed disagreement alongside their byte
   profiles; do not infer consensus from compression alone.
4. For an MDL comparison, specify a candidate common explanation and encode
   both the candidate and the residual information needed to reconstruct each
   answer. Use the same canonicalization and compressor for every candidate.
5. Repeat on held-out topics and report the complete profile, failures, and
   disagreement. Treat thresholds as preregistered experimental criteria, not
   universal constants.

The description length of normalization is part of the model: if alignment,
canonicalization, or filtering is needed to make answers converge, record that
procedure and its cost rather than treating it as free. A future compressor
ensemble can report the minimum observed length across named compressors; it
should retain each individual result and must not present that minimum as a
formal Kolmogorov bound.
