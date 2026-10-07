"""Multi-agent admission checks for curvature-preserving invariant actions."""

from dataclasses import dataclass
import hashlib
import math
from numbers import Integral, Real
from collections.abc import Mapping, Sequence
from typing import Any, Callable


@dataclass(frozen=True)
class AdmissionCandidate:
    name: str
    transform: Callable[[Any], Any]
    preserves_curvature: bool
    preserves_topology_flow: bool
    observe: Callable[[Any], bool]
    curvature_continuous: Callable[[Any], bool]


@dataclass(frozen=True)
class AdmissionResult:
    name: str
    admitted: bool
    curvature_preserved: bool
    topology_flow_preserved: bool
    massless_states_preserved: bool
    massless_states_observed: bool
    false_invariant_count: int
    curvature_drift: float
    residue_score: float
    curvature_continuous: bool
    residue_minimized: bool


def _finite_number(value, name):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite real number")
    return float(value)


def _state_value(state, key):
    if not isinstance(state, Mapping) or key not in state:
        raise ValueError(f"state must contain '{key}'")
    return _finite_number(state[key], key)


def _predicate(value, name):
    if not isinstance(value, bool):
        raise ValueError(f"{name} must return a boolean")
    return value


def _candidate_metrics(candidate, cycle, massless_states):
    topology = _predicate(
        candidate.preserves_topology_flow, "preserves_topology_flow"
    )
    curvature_preserved = _predicate(
        candidate.preserves_curvature, "preserves_curvature"
    )
    massless_preserved = True
    observed = True
    for state in massless_states:
        transformed = candidate.transform(state)
        if _state_value(transformed, "kappa") != 0 or _state_value(transformed, "rho") != 0:
            massless_preserved = False
        observed = observed and _predicate(
            candidate.observe(transformed), "observe"
        )

    false_invariants = 0
    drift = 0.0
    residue_score = 0.0
    continuous = True
    for state in cycle:
        transformed = candidate.transform(state)
        kappa_before = _state_value(state, "kappa")
        kappa_after = _state_value(transformed, "kappa")
        drift += abs(kappa_after - kappa_before)
        residue_score += abs(_state_value(transformed, "rho"))
        if _state_value(transformed, "kappa_p") != _state_value(transformed, "kappa_s"):
            false_invariants += 1
        continuous = continuous and _predicate(
            candidate.curvature_continuous(transformed), "curvature_continuous"
        )

    return {
        "topology": topology,
        "curvature_preserved": curvature_preserved,
        "massless_preserved": massless_preserved,
        "observed": observed,
        "false_invariants": false_invariants,
        "drift": drift,
        "residue_score": residue_score,
        "continuous": continuous,
    }


def evaluate_admission(candidates, cycle, massless_states):
    """Return admission results for candidates over mapping-based geometric states.

    States must provide finite ``kappa`` and ``rho`` values; cycle states also
    provide finite ``kappa_p`` and ``kappa_s`` values. Candidate callbacks
    implement the otherwise domain-specific topology, observation, and local
    curvature-continuity checks.
    """
    candidates = tuple(candidates)
    cycle = tuple(cycle)
    massless_states = tuple(massless_states)
    if any(not isinstance(candidate, AdmissionCandidate) for candidate in candidates):
        raise TypeError("candidates must contain AdmissionCandidate instances")
    if any(not callable(candidate.transform) or not callable(candidate.observe)
           or not callable(candidate.curvature_continuous) for candidate in candidates):
        raise TypeError("candidate actions and predicates must be callable")
    if any(not isinstance(candidate.name, str) or not candidate.name for candidate in candidates):
        raise ValueError("candidate names must be non-empty strings")
    if len({candidate.name for candidate in candidates}) != len(candidates):
        raise ValueError("candidate names must be unique")
    for state in massless_states:
        if _state_value(state, "kappa") != 0 or _state_value(state, "rho") != 0:
            raise ValueError("massless_states must have zero kappa and rho")
    for state in cycle:
        for key in ("kappa", "rho", "kappa_p", "kappa_s"):
            _state_value(state, key)

    metrics = [
        _candidate_metrics(candidate, cycle, massless_states)
        for candidate in candidates
    ]
    minimum_residue = min((metric["residue_score"] for metric in metrics), default=0.0)
    results = []
    for candidate, metric in zip(candidates, metrics):
        residue_minimized = metric["residue_score"] == minimum_residue
        drift_is_zero = metric["drift"] == 0
        life_valued = (
            metric["continuous"]
            and metric["massless_preserved"]
            and drift_is_zero
            and residue_minimized
        )
        admitted = (
            metric["curvature_preserved"]
            and
            metric["topology"]
            and metric["massless_preserved"]
            and metric["observed"]
            and metric["false_invariants"] == 0
            and life_valued
        )
        results.append(AdmissionResult(
            name=candidate.name,
            admitted=admitted,
            curvature_preserved=metric["curvature_preserved"],
            topology_flow_preserved=metric["topology"],
            massless_states_preserved=metric["massless_preserved"],
            massless_states_observed=metric["observed"],
            false_invariant_count=metric["false_invariants"],
            curvature_drift=metric["drift"],
            residue_score=metric["residue_score"],
            curvature_continuous=metric["continuous"],
            residue_minimized=residue_minimized,
        ))
    return results


def commit_torsion(previous_hash, geometric_state, derive_components, modulus):
    """Return ``(t_n, h_{n+1})`` using components derived from geometric state."""
    if not isinstance(modulus, Integral) or isinstance(modulus, bool) or modulus <= 1:
        raise ValueError("modulus must be an integer greater than one")
    modulus = int(modulus)
    if not callable(derive_components):
        raise TypeError("derive_components must be callable")
    if isinstance(previous_hash, bytes):
        previous_digest = previous_hash
    elif isinstance(previous_hash, str):
        try:
            previous_digest = bytes.fromhex(previous_hash)
        except ValueError as error:
            raise ValueError("previous_hash must be a 32-byte SHA-256 digest") from error
    else:
        raise TypeError("previous_hash must be a hexadecimal string or bytes")
    if len(previous_digest) != hashlib.sha256().digest_size:
        raise ValueError("previous_hash must be a 32-byte SHA-256 digest")

    components = derive_components(geometric_state)
    if not isinstance(components, Sequence) or isinstance(components, (str, bytes)) or len(components) != 3:
        raise ValueError("derive_components must return three integer components")
    if any(not isinstance(value, Integral) or isinstance(value, bool) for value in components):
        raise ValueError("torsion components must be integers")
    torsion = sum(int(value) for value in components) % modulus
    width = max(1, ((modulus - 1).bit_length() + 7) // 8)
    encoded_torsion = torsion.to_bytes(width, "big")
    commitment = hashlib.sha256(previous_digest + encoded_torsion).hexdigest()
    return torsion, commitment
