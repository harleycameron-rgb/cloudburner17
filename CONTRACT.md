# Stabiliser Contract

Cloudburner17 is the invariant stabiliser substrate for the constellation.  
All dependent repos must route lifecycle events through this gate.  
This contract defines the non-negotiable rules governing stabiliser interaction.

## Immutable Principles
1. Precursor repos retain their original structural provenance.
2. Cloudburner17 cannot override or challenge precursor structural qualities.
3. Burn semantics apply only from the moment the gate is installed.
4. Timestamp invariance is enforced forward, not retroactively.
5. All lifecycle transitions must pass through the stabiliser gate.
6. Drift relative to original provenance must be detected and reported.
7. Cloudburner17 is the stabiliser, not the origin.

## Obligations of Dependent Repos
- Must use computeTrajectory for ancestry mapping.
- Must use burnModule for lifecycle transitions.
- Must use verifyTimestampProof for external attestation.
- Must not redefine lifecycle semantics internally.
- Must not bypass the stabiliser boundary.

## Stabiliser Authority
Cloudburner17 enforces deterministic ancestry, unified burn semantics,  
and timestamp invariance across all constellation repos.  
It stabilises behaviour but does not rewrite origin geometry.
