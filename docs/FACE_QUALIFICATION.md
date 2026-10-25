# Strict face qualification registry (PR 1)

Run: node --test tests/face_qualification.test.js
Additive dependency-free ES module; existing admission.py and runtime wiring unchanged.

Trusted bootstrap creates the authority with fixed bindings, approved validator digests,
and a synchronous independent evaluate callback. Never construct authority from request
payloads or expose management methods to clients. Expose only verifier. The callback must
validate bound evidence, not echo supplied predicates. Tests use mock evaluators to test
registry enforcement, not geometric truth. sealQualification hashes; it grants no authority.

Schema 1.0.0 uses exact plain own-data-property objects, ASCII identifiers (128 characters
maximum), non-negative safe integer ticks, exact true S/B/F/G/R/A/C/P predicates and
mandatory lowercase SHA-512 hex (128 characters) for all digest fields, including alternate
and counter evidence. This intentionally differs from older illustrative formats; no
implicit SHA-256 migration is allowed. Hash domain is
waxtablet/face-qualification/1.0.0/<face> followed by a NUL byte. Body keys and predicate
keys are sorted, JSON is compact, and the commitment field is excluded. This restricted
encoding is not a general JSON canonicalization standard. Tests include a literal digest
computed independently with Python json/hashlib.

Issuance keeps frozen records; replacement supersedes the current face. Explicit revoked
and invalidated statuses are terminal. Unique event IDs and increasing per-face ticks
prevent replay within this authority only. Restart loses state. New epoch/origin/profile
requires deactivation and a fresh trusted authority. No clock expiry is implemented.
Validator withdrawal and session deactivation invalidate verification. Every authority
change increments a version. Reentrant changes during evaluation reject issuance.

checkSix returns VERIFIED, not PREPARED or COMMITTED. It requires Tap, Surface, Gain,
Habitat, Engine, Business; a missing face blocks. Eight UI arms cannot substitute.
It does not persist, compute a center, dispatch commands, or enable live receipt writes.
The returned capabilities separate trusted management from verification; they are not a
sandbox against malicious same-process code. Parse untrusted JSON into ordinary objects;
Proxy objects and hostile same-process code are outside this boundary. No signatures,
external notarization, cross-process registry, distributed replay protection, production
geometry validator or deployment is claimed. PR 2 must supply persistent consistent
snapshots and atomic commitment/revocation. Actual geometry/evidence evaluation, artifact
authenticity and service authentication remain integration prerequisites.
