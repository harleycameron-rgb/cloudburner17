# CloudBurner17 MDL system snapshot — 2026-11-20

## Provenance
- Base main commit inspected: `ea906789dcc72d4b561ec78f61a0e77bd35a45d8`.
- Working branch: `feature/mdl-coding-agent-plan-v1`.
- Tracking issue: #71; draft review: #72.
- This document records repository source changes, not running service state.

## Cycle 1 — MDL → implementation
- `src/coding_agent_plan.py`: deterministic PLAN_ONLY contract, exact source SHA allowlist, bounded paths and iterations, SHA-256 receipt.
- `tests/test_coding_agent_plan.py`: synthetic positive and negative controls.
- Status: IMPLEMENTED in branch; tests NOT EXECUTED; CI UNVERIFIED.

## Cycle 2 — MDL → implementation
- `src/coding_agent_reader.py`: injected read-only source capability; explicit pinned SHA; byte bound and per-file digest; no built-in network access or credentials.
- `tests/test_coding_agent_reader.py`: read-boundary tests and failure controls.
- Status: IMPLEMENTED in branch; tests NOT EXECUTED; reader authenticity UNVERIFIED.

## Cycle 3 — MDL / next smallest action
- Obtain focused test evidence:
  `python -B -m unittest discover -s tests -p 'test_coding_agent_*.py' -v`.
- Obtain existing CI/regression results and diagnose the failed `scandoc-zero` Vercel preview check. A Vercel status failure is not proof of a production outage.
- Add an optional **separate** GitHub transport only after verifying exact-ref behavior and installation permissions.
- Add branch/draft-PR writer only with explicit per-task approval and tests; no auto-merge.

## Constraints
- Zero-data runtime unchanged; native gate CLOSED.
- No live LLM calls, charges, DNS, repository visibility changes, production promotion, native firing or sphere writes.
- No claim of 40/40 CloudBurner17 runtime repository access.
- GitHub App access through a chat connector is distinct from deployed CloudBurner17 authentication.
- Vercel Git connections were previously observed for `cloudburner17` across both teams; website health must be tested independently.

## MDL statuses
| Capability | Status | Evidence |
| --- | --- | --- |
| Deterministic plan boundary | IMPLEMENTED | `src/coding_agent_plan.py` |
| Injected read-only source adapter | IMPLEMENTED | `src/coding_agent_reader.py` |
| Focused local tests | UNVERIFIED | Tests authored, not executed |
| CI regression | UNVERIFIED | No passing run established |
| Authenticated GitHub transport | NOT IMPLEMENTED | Only injected capability exists |
| Repository edits / draft PR automation | NOT IMPLEMENTED | No writer exists |
| Persistent task execution | NOT IMPLEMENTED | No worker configured |
| Production deployment | NOT IMPLEMENTED | Not authorized |

## Owner checkpoint
No owner action is required to review these draft changes. To **merge** or enable real repository write operations, require a separate explicit approval after successful tests and security review.
