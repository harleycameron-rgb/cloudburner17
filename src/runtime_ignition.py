"""In-memory runtime ignition sequence for invariant-admitted candidates."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math
from numbers import Integral, Real
import re
from typing import Any, Callable

if __package__:
    from .admission import (
        AdmissionCandidate,
        AdmissionResult,
        commit_torsion,
        evaluate_admission,
    )
else:
    from admission import (
        AdmissionCandidate,
        AdmissionResult,
        commit_torsion,
        evaluate_admission,
    )


@dataclass(frozen=True)
class RuntimeAssets:
    """Already-loaded runtime contracts; constructing or validating these does no file I/O."""

    topology_map: str
    curvature_flow: str
    residue_state: Real
    massless_states: Sequence[Mapping[str, Any]]
    torsion_modulus: int
    genesis_hash: str


@dataclass(frozen=True)
class IgnitionState:
    root: str | None


class IgnitionStub:
    name = "IgnitionStub"

    def __init__(self):
        self.state = IgnitionState(root=None)

    def ignite(self):
        self.state = IgnitionState(root=f"{self.name}:root")
        return self.state

    def diagnostic(self):
        return f"{self.name} stable"


class ScanDocIgnitionStub(IgnitionStub):
    name = "ScanDocIgnitionStub"


class InvariantSurfaceIgnitionStub(IgnitionStub):
    name = "InvariantSurfaceIgnitionStub"


class TopologyEngineIgnitionStub(IgnitionStub):
    name = "TopologyEngineIgnitionStub"


class WaxtabletIgnitionStub(IgnitionStub):
    name = "WaxtabletIgnitionStub"


class OrreryIgnitionStub(IgnitionStub):
    name = "OrreryIgnitionStub"


class SentinelDotIgnitionStub(IgnitionStub):
    name = "SentinelDotIgnitionStub"


_IGNITION_STUBS = (
    ScanDocIgnitionStub,
    InvariantSurfaceIgnitionStub,
    TopologyEngineIgnitionStub,
    WaxtabletIgnitionStub,
    OrreryIgnitionStub,
    SentinelDotIgnitionStub,
)


class RuntimeIgnitionError(RuntimeError):
    """Raised when any runtime ignition contract fails."""


@dataclass(frozen=True)
class RuntimeIgnitionResult:
    status: str
    candidate: AdmissionResult
    legs: tuple[IgnitionStub, ...]
    topology_runtime: str
    massless_runtime: tuple[Mapping[str, Any], ...]
    torsion_runtime: Mapping[int, int]
    hash_runtime: Mapping[int, str]


def _finite_real(value, label):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise RuntimeIgnitionError(f"{label} must be a finite real number")
    return float(value)


def _validate_assets(assets):
    if not isinstance(assets, RuntimeAssets):
        raise TypeError("assets must be a RuntimeAssets instance")
    if not isinstance(assets.topology_map, str) or not assets.topology_map.strip():
        raise RuntimeIgnitionError("pre-ignition check failed: topology map is not loaded")
    if not isinstance(assets.curvature_flow, str) or not assets.curvature_flow.strip():
        raise RuntimeIgnitionError("pre-ignition check failed: curvature.flow is not readable")
    if _finite_real(assets.residue_state, "residue.state") != 0:
        raise RuntimeIgnitionError("pre-ignition check failed: residue.state is not initialized to 0")
    if (
        not isinstance(assets.massless_states, Sequence)
        or isinstance(assets.massless_states, (str, bytes))
        or not assets.massless_states
    ):
        raise RuntimeIgnitionError("pre-ignition check failed: massless.index must contain an element")
    if (
        not isinstance(assets.torsion_modulus, Integral)
        or isinstance(assets.torsion_modulus, bool)
        or assets.torsion_modulus <= 1
    ):
        raise RuntimeIgnitionError("pre-ignition check failed: torsion.mod is uncorrupted")
    if not isinstance(assets.genesis_hash, str) or not re.fullmatch(
        r"[0-9a-fA-F]{64}", assets.genesis_hash
    ):
        raise RuntimeIgnitionError("pre-ignition check failed: hash.commit has no valid genesis h0")
    for state in assets.massless_states:
        if not isinstance(state, Mapping):
            raise RuntimeIgnitionError("massless.index entries must be state mappings")
        if _finite_real(state.get("kappa"), "massless kappa") != 0 or _finite_real(
            state.get("rho"), "massless rho"
        ) != 0:
            raise RuntimeIgnitionError("massless.index contains a non-massless state")


def run_runtime_ignition(
    candidates,
    cycle,
    assets,
    derive_components: Callable[[Any], Sequence[int]],
    candidate_name=None,
):
    """Validate, admit, and ignite one candidate using preloaded in-memory assets.

    Any required filesystem ingestion must happen outside this function and before
    the zero-data audit guard is installed.
    """
    _validate_assets(assets)
    candidates = tuple(candidates)
    cycle = tuple(cycle)
    if not cycle:
        raise RuntimeIgnitionError("runtime ignition requires at least one cycle state")
    if candidate_name is None:
        if len(candidates) != 1:
            raise ValueError("candidate_name is required when evaluating multiple candidates")
        candidate_name = candidates[0].name
    selected = next(
        (candidate for candidate in candidates if candidate.name == candidate_name),
        None,
    )
    if selected is None:
        raise ValueError(f"candidate '{candidate_name}' is not in the candidate set")

    legs = tuple(stub_type() for stub_type in _IGNITION_STUBS)
    for leg in legs:
        leg.ignite()
        if leg.state.root is None or "stable" not in leg.diagnostic().lower():
            raise RuntimeIgnitionError(f"zero-state emitter failed: {leg.name}")

    massless_states = tuple(assets.massless_states)
    for state in massless_states:
        continuous = selected.curvature_continuous(state)
        if not isinstance(continuous, bool):
            raise RuntimeIgnitionError("curvature continuity predicate must return a boolean")
        if not continuous:
            raise RuntimeIgnitionError("massless convergent lock-in failed: curvature is not continuous")

    if selected.preserves_topology_flow is not True:
        raise RuntimeIgnitionError("topology preservation seal failed")

    results = evaluate_admission(candidates, cycle, massless_states)
    result_by_name = {result.name: result for result in results}
    admission = result_by_name[candidate_name]

    if not admission.massless_states_preserved:
        raise RuntimeIgnitionError("massless-state preservation seal failed")
    if not admission.massless_states_observed:
        raise RuntimeIgnitionError("observation channel ignition failed")
    if admission.false_invariant_count:
        raise RuntimeIgnitionError(
            f"false-invariant purge: candidate '{candidate_name}' has "
            f"{admission.false_invariant_count} false invariant(s)"
        )
    if not admission.admitted:
        raise RuntimeIgnitionError(f"final admission predicate rejected '{candidate_name}'")
    if admission.residue_score != 0:
        raise RuntimeIgnitionError("cyclic ignition requires residue to remain 0")
    if not callable(derive_components):
        raise TypeError("derive_components must be callable")

    torsion_runtime = {}
    hash_runtime = {0: assets.genesis_hash.lower()}
    previous_hash = assets.genesis_hash
    for index, state in enumerate(cycle):
        torsion, previous_hash = commit_torsion(
            previous_hash, state, derive_components, assets.torsion_modulus
        )
        torsion_runtime[index] = torsion
        hash_runtime[index + 1] = previous_hash

    return RuntimeIgnitionResult(
        status="LIVE",
        candidate=admission,
        legs=legs,
        topology_runtime=assets.topology_map,
        massless_runtime=massless_states,
        torsion_runtime=torsion_runtime,
        hash_runtime=hash_runtime,
    )
