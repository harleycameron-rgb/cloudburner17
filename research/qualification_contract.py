"""Offline-only six-face policy evaluation. NOT trusted qualification or a live gate."""
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from math import isfinite

FACES = ("tap", "surface", "gain", "habitat", "engine", "business")

class SemanticState(str, Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    DISPROVEN = "disproven"
    UNKNOWN = "unknown"

@dataclass(frozen=True)
class PolicyDecision:
    accepted: bool
    reasons: tuple[str, ...]
    advisory_score: float | None
    authority: str = "OFFLINE_POLICY_ONLY"
    live_gate: str = "CLOSED"
    sphere_writes: bool = False

def evaluate_faces(faces: Mapping[str, object], *, score=None) -> PolicyDecision:
    """Six explicit face predicates. Scores never supersede an unmet predicate."""
    reasons = []
    if not isinstance(faces, Mapping):
        return PolicyDecision(False, ("invalid_face_map",), None)
    missing = sorted(set(FACES) - set(faces))
    extra = sorted(set(faces) - set(FACES), key=str)
    if missing:
        reasons.append("missing_faces:" + ",".join(missing))
    if extra:
        reasons.append("unexpected_faces:" + ",".join(map(str, extra)))
    for face in FACES:
        if face not in faces:
            continue
        record = faces[face]
        if not isinstance(record, Mapping):
            reasons.append(face + ":invalid_record")
            continue
        if set(record) != {"semantic_state", "geometry_ok", "provenance_ok"}:
            reasons.append(face + ":invalid_fields")
            continue
        try:
            state = SemanticState(record["semantic_state"])
        except (ValueError, TypeError):
            reasons.append(face + ":invalid_semantic_state")
            continue
        if state is not SemanticState.SUPPORTED:
            reasons.append(face + ":" + state.value)
        if record["geometry_ok"] is not True:
            reasons.append(face + ":geometry_unverified")
        if record["provenance_ok"] is not True:
            reasons.append(face + ":provenance_unverified")
    advisory_score = None
    if score is not None:
        if type(score) not in (int, float) or not isfinite(score) or not 0 <= score <= 1:
            reasons.append("invalid_advisory_score")
        else:
            advisory_score = float(score)
    return PolicyDecision(not reasons, tuple(reasons), advisory_score)
