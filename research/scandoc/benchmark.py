"""Pure bounded experiments. No providers, renderer, runtime gates, or file I/O."""

from copy import deepcopy
import hashlib
import itertools
import json
import math
import re
from statistics import mean

from src.benchmark_agent import parabolic_step_down, phi
from src.tentacled_sphere import TentacledSphere

from .fixtures import CONTRACT, FIXTURE_VERSION, POLICY_VERSION, SEMANTIC


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )


def commitment(value):
    return hashlib.sha512(canonical(value).encode("utf-8")).hexdigest()


def _number(value, bound=1e6):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or abs(value) > bound):
        raise ValueError("expected a bounded finite real number")
    return float(value)


def _vector(value):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError("expected three coordinates")
    return [_number(x) for x in value]


def _points(value):
    if not isinstance(value, (list, tuple)) or not 1 <= len(value) <= 32:
        raise ValueError("expected 1..32 points")
    return [_vector(point) for point in value]


def _distance(a, b):
    return math.dist(a, b)


def _symbols(responses):
    if not isinstance(responses, list) or not 2 <= len(responses) <= 32:
        raise ValueError("expected 2..32 responses")
    for response in responses:
        if not isinstance(response, list) or not 1 <= len(response) <= 128:
            raise ValueError("expected 1..128 annotated symbols per response")
        if any(not isinstance(s, str) or not re.fullmatch(r"[a-zA-Z0-9:_-]{1,80}", s)
               for s in response):
            raise ValueError("expected bounded symbolic annotations")
    return [set(response) for response in responses]


def semantic_control(responses, representation):
    original = _symbols(responses)
    if representation == "identity":
        encode = lambda symbol: symbol
    elif representation == "coarse":
        encode = lambda symbol: "generic"
    elif representation == "distinction-preserving":
        encode = lambda symbol: "encoded:" + symbol
    else:
        raise ValueError("unsupported representation")
    vocabulary = set.union(*original)
    inverse = {}
    for symbol in sorted(vocabulary):
        inverse.setdefault(encode(symbol), []).append(symbol)
    retained = sorted(s for group in inverse.values() if len(group) == 1 for s in group)
    represented = [{encode(s) for s in response} for response in original]
    overlap = mean(
        len(a & b) / len(a | b) for a, b in itertools.combinations(represented, 2)
    )
    positive = [i for i, r in enumerate(original) if "claim:p" in r]
    negative = [i for i, r in enumerate(original) if "claim:not-p" in r]
    return {
        "representation": representation,
        "overlap_jaccard": overlap,
        "retained_distinctions": retained,
        "retention_fraction": len(retained) / len(vocabulary),
        "discarded_information": sorted(vocabulary - set(retained)),
        "input_symbol_count": sum(len(r) for r in responses),
        "output_unique_symbol_count": sum(len(r) for r in represented),
        "size_metric": "symbol-count proxy; not validated semantic MDL",
        "represented": [sorted(r) for r in represented],
        "raw_annotations": deepcopy(responses),
        "contradiction": {
            "positive_responses": positive, "negative_responses": negative,
            "present_in_input": bool(positive and negative),
            "visible_in_representation": bool(
                positive and negative and encode("claim:p") != encode("claim:not-p")
            ),
        },
    }


def adapt_recorded(council, annotations, origin="recorded"):
    """Adapt CouncilResult.to_dict() with caller-supplied, unvalidated annotations.

    Never infer meaning or successful evidence from model prose. Preserve raw
    responses in memory only; CLI export accepts built-in synthetic fixtures only.
    """
    if origin not in ("recorded", "external"):
        raise ValueError("recorded/external origin required")
    if not isinstance(council, dict) or not isinstance(council.get("rounds"), list):
        raise ValueError("missing recorded rounds")
    if not 1 <= len(council["rounds"]) <= 32:
        raise ValueError("expected 1..32 recorded rounds")
    replies = []
    for round_ in council["rounds"]:
        if not isinstance(round_, dict) or not isinstance(round_.get("replies"), list):
            raise ValueError("missing recorded replies")
        replies.extend(round_["replies"])
        if len(replies) > 32:
            raise ValueError("at most 32 recorded replies")
    _symbols(annotations)
    if len(replies) != len(annotations):
        raise ValueError("annotations must correspond to every recorded reply")
    observations = []
    for reply, symbols in zip(replies, annotations):
        if not isinstance(reply, dict):
            raise ValueError("invalid recorded reply")
        content = reply.get("content")
        if content is not None and (not isinstance(content, str) or len(content) > 100000):
            raise ValueError("invalid recorded content")
        status = "unverified"
        if not content:
            status = "missing"
        elif content.startswith(("[ERROR]", "[Chairman error]")):
            status = "failed"
        observations.append({
            "origin": origin, "status": status, "raw": deepcopy(reply),
            "annotations": list(symbols),
        })
    return {"observations": observations, "claim": claim_gate(observations)}


def claim_gate(evidence):
    """A fail-closed bounded claim gate, never a lifecycle authorization."""
    if not isinstance(evidence, list) or not evidence:
        return {"status": "unresolved", "reasons": ["missing evidence"]}
    reasons = []
    for item in evidence:
        if not isinstance(item, dict) or item.get("status") != "verified":
            reasons.append("failed, missing, unsupported or unverified evidence")
        elif item.get("origin") != "synthetic" or item.get("check") is not True:
            reasons.append("only explicitly checked synthetic controls are supported")
    return {
        "status": "unresolved" if reasons else "bounded-synthetic-only",
        "reasons": sorted(set(reasons)),
    }


def geometry_controls(raw):
    if not isinstance(raw, list) or not 2 <= len(raw) <= 32:
        raise ValueError("expected 2..32 snapshots")
    frames = [_points(frame) for frame in raw]
    if len({len(frame) for frame in frames}) != 1:
        raise ValueError("point identities must persist across frames")
    tolerance = CONTRACT["geometry"]["tolerance"]
    rotated = [[[-p[1], p[0], p[2]] for p in frame] for frame in frames]
    translated = [[[p[0] + 2, p[1] - 3, p[2] + 1] for p in frame]
                  for frame in rotated]
    deformed = deepcopy(frames)
    for frame in deformed:
        frame[0][0] += 0.25
    order = CONTRACT["geometry"]["shuffle_order"] if len(frames) == 4 else list(
        reversed(range(len(frames)))
    )
    variants = {
        "rotation": rotated, "coordinate-frame": translated,
        "single-arm-deformation": deformed,
        "shuffled-time": [deepcopy(frames[i]) for i in order],
    }

    def distances(frame):
        return [_distance(a, b) for a, b in itertools.combinations(frame, 2)]

    def path(series):
        return math.fsum(_distance(a, b) for f, g in zip(series, series[1:])
                         for a, b in zip(f, g))

    baseline = [distances(frame) for frame in frames]
    results = {}
    for name, changed in variants.items():
        if len(frames[0]) < 2:
            results[name] = {"status": "unsupported", "reason": "pair distances need two arms"}
            continue
        # A shuffled snapshot retains its spatial identity, not its time index.
        references = [frames[i] for i in order] if name == "shuffled-time" else frames
        reference_distances = ([baseline[i] for i in order]
                               if name == "shuffled-time" else baseline)
        error = max(abs(a - b) for ref, frame in zip(reference_distances, changed)
                    for a, b in zip(ref, distances(frame)))
        residues = []
        for ref, frame in zip(references, changed):
            for p, q in zip(ref, frame):
                delta = [b - a for a, b in zip(p, q)]
                if math.hypot(*p) == 0:
                    residues.append({"status": "unsupported", "reason": "zero radial reference"})
                    continue
                normal = phi(p)
                scalar = math.fsum(a * b for a, b in zip(delta, normal))
                n = [scalar * x for x in normal]
                tangent = [a - b for a, b in zip(delta, n)]
                reconstruction = [a + b for a, b in zip(tangent, n)]
                residues.append({
                    "status": "observed", "normal_vector": n, "tangent_vector": tangent,
                    "normal_norm": math.hypot(*n), "tangent_norm": math.hypot(*tangent),
                    "reconstruction_error": _distance(delta, reconstruction),
                })
        results[name] = {
            "status": "invariant-preserved" if error <= tolerance else "falsified",
            "failure_reasons": [] if error <= tolerance else [
                "declared labeled pair-distance invariant exceeded tolerance"
            ],
            "max_pair_distance_error": error,
            "path_length": path(changed),
            "path_length_change": path(changed) - path(frames),
            "residue": residues,
            "transformed_inputs": changed,
            "temporal_order": order if name == "shuffled-time" else list(range(len(frames))),
        }
    return {
        "raw_inputs": deepcopy(raw), "baseline_path_length": path(frames),
        "controls": results,
        "boundary-removal": {"status": "unsupported", "reason": "no boundary manifold supplied"},
        "boundary-replacement": {"status": "unsupported", "reason": "no replacement law supplied"},
        "tap-surface": {
            "status": "unsupported",
            "reason": "runtime/touch_surface_pair.py absent from audited source revision",
        },
        "trajectory_claim": "observed stability only; prescribed seed trajectory has no update operator",
    }


def fit_training(training):
    points = _points(training)
    target = [mean(p[i] for p in points) for i in range(3)]
    return {"target": target, "noise_floor_training_only": max(
        _distance(p, target) for p in points
    )}


def recovery_control(training, held_out, perturbation):
    model = fit_training(training)
    held_out = _points(held_out)
    perturbation = _vector(perturbation)
    policy = CONTRACT["recovery"]
    if math.hypot(*perturbation) > policy["max_perturbation"]:
        raise ValueError("perturbation exceeds declared bound")
    target = model["target"]
    trials = []
    for point in held_out:
        baseline, perturbed = list(point), [a + b for a, b in zip(point, perturbation)]
        errors = [_distance(baseline, perturbed)]
        for _ in range(policy["steps"]):
            baseline = parabolic_step_down(baseline, target, control_offset=0.7, t=0.25)
            perturbed = parabolic_step_down(perturbed, target, control_offset=0.7, t=0.25)
            errors.append(_distance(baseline, perturbed))
        trials.append({
            "paired_perturbation_errors": errors,
            "final_distance_to_training_target": _distance(perturbed, target),
            "within_training_calibration": _distance(perturbed, target)
            <= model["noise_floor_training_only"],
        })
    return {
        "status": "observed", "operator": policy["operator"],
        "model": model, "training": deepcopy(training), "held_out": held_out,
        "perturbation": perturbation, "trials": trials,
        "claim": "bounded recovery under declared synthetic operator only",
    }


def run(source_revision):
    if not isinstance(source_revision, str) or not re.fullmatch(r"[0-9a-f]{40}", source_revision):
        raise ValueError("source revision must be a full lowercase git SHA")
    geometry = CONTRACT["geometry"]
    frames = []
    for tick in range(geometry["ticks"]):
        sphere = TentacledSphere(
            seed=geometry["seed"] + tick * geometry["time_step"], delta=geometry["delta"]
        )
        frames.append([entry["vector"] for entry in sphere.actuate().values()])
    recovery = CONTRACT["recovery"]
    content = {
        "schema": "scandoc-evidence/1",
        "source_revision": source_revision,
        "source_revision_trust": "caller assertion; not a signed provenance receipt",
        "fixture_version": FIXTURE_VERSION, "policy_version": POLICY_VERSION,
        "observation_origin": "synthetic",
        "configuration": deepcopy(CONTRACT),
        "semantic": {
            name: {variant: semantic_control(responses, variant)
                   for variant in CONTRACT["semantic"]["representations"]}
            for name, responses in SEMANTIC.items()
        },
        "geometry": geometry_controls(frames),
        "recovery": recovery_control(
            recovery["training"], recovery["held_out"], recovery["perturbation"]
        ),
        "research_claim": {
            "status": "unresolved",
            "reasons": [
                "no validated semantic MDL metric",
                "prescribed sphere trajectory is not evidence of attraction",
                "Tap-Surface integration and boundary comparisons unsupported",
                "no physical coupling or independent measured evidence",
            ],
        },
    }
    content["geometry"]["point_order"] = list(sphere.tentacles)
    content["geometry"]["ticks"] = list(range(geometry["ticks"]))
    content["geometry"]["times"] = [
        tick * geometry["time_step"] for tick in range(geometry["ticks"])
    ]
    return {
        "content": content, "content_commitment": commitment(content),
        "geometry_commitment": commitment(content["geometry"]),
    }


def replay(evidence):
    """Check commitment AND independently re-execute the versioned controls."""
    try:
        if not isinstance(evidence, dict) or set(evidence) not in (
            {"content", "content_commitment", "geometry_commitment"},
            {"content", "content_commitment", "geometry_commitment", "event"}
        ):
            raise ValueError("invalid evidence envelope")
        if "event" in evidence:
            event = evidence["event"]
            if (not isinstance(event, dict) or set(event) != {"exported_at"}
                    or not isinstance(event["exported_at"], str) or len(event["exported_at"]) > 80):
                raise ValueError("invalid event metadata")
        content = evidence["content"]
        if commitment(content) != evidence["content_commitment"]:
            raise ValueError("content commitment mismatch")
        if commitment(content["geometry"]) != evidence["geometry_commitment"]:
            raise ValueError("geometry commitment mismatch")
        expected = run(content["source_revision"])
        if canonical(content) != canonical(expected["content"]):
            raise ValueError("re-executed metrics or policy mismatch")
        return {"status": "verified", "scope": "synthetic replay only"}
    except (ValueError, TypeError, KeyError, OverflowError) as error:
        return {"status": "rejected", "reason": str(error)}
