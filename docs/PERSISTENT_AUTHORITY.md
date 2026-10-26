# PR 2: persistent authority and transactional center commitment

Opt-in infrastructure only. Existing engine runtime, PR 1 JavaScript, production endpoints,
DNS and live gate remain unchanged. Store is a privileged management capability: never
expose create/issue/change/commit directly to untrusted clients. Trusted bootstrap owns DB
credentials and supplies an independent synchronous evidence evaluator. It must inspect
bound evidence, not echo submitted flags. Tests use mock evaluators, not scientific proof.
writes_authorized is a local safety interlock, NOT authentication.

PostgreSQL is the intended shared backend; install psycopg2-binary==2.9.10. SQLite is the
single-host executable reference, not a production substitution. Use protected local files,
not network/replicated SQLite. Explicit migrate() creates waxtablet_authority_v1; no import
opens a DB or migrates it. Use separate migration credentials and least privilege.

Each session stores bounded registry state (10,000 records maximum), version and center in
one row. PostgreSQL READ COMMITTED plus SELECT FOR UPDATE serializes same-session changes;
SQLite BEGIN IMMEDIATE serializes writers. Updates also compare expected version. Direct
SQL bypassing this protocol is unsupported. DB administrators are inside the trust boundary.
Full state documents are rewritten; no high-throughput or sharding claim is made. Benchmark
and normalize storage before large deployment. Evaluators run under lock: keep them bounded,
non-reentrant, deterministic and without external I/O. Exceptions roll back issuance.

Records use PR 1 schema 1.0.0, mandatory SHA-512 evidence digests, exact fields and true
S/B/F/G/R/A/C/P predicates, ASCII identifiers and safe integer ticks. No silent SHA-256
migration. Replay events, ticks, selection, supersession, terminal revocation/invalidation,
validator withdrawal and deactivation persist across restarts. Session IDs cannot be reused;
rotate by deactivating and explicitly creating a new session/epoch with fresh qualifications.
No wall-clock expiry, signatures, external notarization or validator authenticity is supplied.

prepare() acquires a consistent lock but changes no rows. It revalidates six selected records
and returns PREPARED plus authority_version and ordered faces. Center domain is independently
versioned waxtablet/center-commitment/1.0.0 followed by one NUL byte and compact sorted-key
UTF-8 JSON, with Tap/Surface/Gain/Habitat/Engine/Business array order. This restricted format
is not general JCS. Literal face and center vectors were generated independently with
Python and Node respectively.

commit() is disabled by default. Trusted authorized code explicitly enables it. Under the
same lock it rebuilds the entire current proposal, compares bytes/version and atomically
stores one center per session. Unchanged retries are idempotent; stale, tampered, reordered,
revoked and withdrawn proposals reject. If revocation wins first, commit fails. If commit
wins first, the center remains historical; later revocation prevents new acceptance/retry.
A historical center is never sufficient current authorization. New cycles need new sessions.

Run: python -m unittest discover -s tests -p test_persistent_authority.py -v
Set WAXTABLET_TEST_POSTGRES_DSN ONLY to a disposable database. Tests leave isolated test
sessions there. Without it PostgreSQL cases explicitly skip. CI creates a disposable
PostgreSQL 16.6 service and runs both backends. Separate-process race tests use independent
connections and barriers while a transaction holds the lock. No production credentials.

Local evidence: 33 passed, 30 PostgreSQL cases skipped, zero failures. PostgreSQL server
and Docker unavailable locally. PostgreSQL CI MUST pass before sign-off. Full repository
suite, service authentication/wiring, real evaluator, load/failover, backup/restore, clock
policy, key custody and operational rollback remain unverified. CI uses version-tagged
actions/image: digest pinning and supply-chain review remain release tasks. This PR does
not authorize merging, production deployment, paid provisioning or live-write activation.
