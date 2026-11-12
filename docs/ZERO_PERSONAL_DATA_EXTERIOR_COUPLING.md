# Zero-personal-data exterior coupling: candidate contract (read-only research)

Status: **PROPOSED / UNVERIFIED**. No connector, engine coupling, native firing, external software or hardware control is authorized by this document.

## Architecture

The post-separation Sphere may consider **public, non-personal, geometry-relevant** data through an *external observer adapter*, not as an additional Cube face or spatial axis. The immutable six-face Cube and its origin/1536 references remain unchanged. The eight Sphere expressions share one committed trajectory. The zero-data boundary is outside the contained dimensional system and supplies only versioned, traceable references.

**Zero personal data** is a stronger requirement than public availability: public datasets can contain location traces, personal identifiers, accounts or device metadata. Reject these rather than relying on public-source status.

## Candidate discovery and coupling gate

1. Root Scour discovers a code or mathematical correspondence, with exact source revision, license, dependency graph, threat model, and a reproducible test fixture.
2. Classify the claim as SUPPORTED, UNSUPPORTED, DISPROVEN or UNKNOWN. Similar code structure or matching hash does not establish geometric invariance.
3. Reject inputs with personal identifiers, individual geolocation, device IDs, credentials, faces/voices, raw user uploads or high-cardinality quasi-identifiers. No raw telemetry, no user profiling.
4. Require a public data license permitting the intended use; pin schema, source, epoch, coordinate frame, units and content digest. Explicitly distinguish hash commitment from trusted time/origin attestation.
5. Validate frame conversion, forward/reverse stream relationships, six-face immutability, eight-expression shared transform, paradox-extreme boundary conditions and a known canary disruptor. Fail closed on unknown mapping.
6. Keep adapters read-only, outbound-disabled by default, with fixed allowlists, bounded size, no dynamic execution, no unreviewed dependencies and no hardware actuation. Network fetches require separate explicit approval and a narrowly scoped proxy.
7. Only after independent tests and explicit review may an exterior software/hardware *interface* be proposed. Hardware actuation requires its own authorization and safety interlocks; it is never granted by Root Scour discovery alone.

## Suggested non-personal source classes

Public astronomical ephemerides, published reference-frame definitions, mathematical geometry libraries and public non-identifying instrument calibration tables are **candidates**, not yet verified connections. Validate license, precision, provenance and semantics for each.

## Viewport output contract

Each candidate should expose: `candidate_id`, `source_revision`, `license`, `schema`, `frame`, `units`, `digest`, `personal_data_check`, `root_scour_evidence`, `geometry_tests`, `semantic_state`, `unknowns`, `native_gate: CLOSED`, `writes_permitted: false`. Reject rather than fabricate absent fields.

## Current limitation

The root canary is synthetic; its zero-filled 384-character marker is **not** a derived 1536-bit commitment. Its reported reference immutability is a local comparison, not independently attested provenance. No real orrery or external topology feed is connected.
