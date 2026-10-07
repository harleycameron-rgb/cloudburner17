import json
import math
from collections.abc import Mapping, Sequence
from numbers import Real

from harmony_stabilizer import HarmonyDriftError, HarmonyStabilizer
from zero_data import assert_no_file_io, install_zero_data_guard


_KNOWN_STEPS = ("burn", "ignite", "residue")


def _finite_number(value):
    return isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(value)


def stabilise_step(step_name, output):
    if not isinstance(step_name, str) or not step_name:
        raise ValueError("step name must be a non-empty string")

    if step_name == "burn":
        if not isinstance(output, Mapping) or set(output) != {"lambda_updated"}:
            raise ValueError("burn output must contain only lambda_updated")
        values = output["lambda_updated"]
        if not isinstance(values, (list, tuple)) or not values or not all(
            _finite_number(value) and value >= 0 for value in values
        ):
            raise ValueError("burn lambda_updated must be a non-empty finite vector")
    elif step_name == "ignite":
        engine = output.get("InvariantEngine") if isinstance(output, Mapping) else None
        if not isinstance(engine, Mapping) or set(engine) != {"sound", "lambda", "times"}:
            raise ValueError("ignite output must contain the InvariantEngine contract")
        if not all(isinstance(engine[key], (list, tuple)) for key in ("sound", "lambda", "times")):
            raise ValueError("ignite sound, lambda, and times must be sequences")
        if not all(_finite_number(value) for value in engine["lambda"]):
            raise ValueError("ignite lambda values must be finite numbers")
    elif step_name == "residue":
        if (
            not isinstance(output, (list, tuple))
            or len(output) != 2
            or not _finite_number(output[0])
            or not isinstance(output[1], str)
        ):
            raise ValueError("residue output must be a finite number and a string tag")

    try:
        json.dumps(output, ensure_ascii=False, allow_nan=False, sort_keys=True)
    except (TypeError, ValueError) as error:
        raise ValueError("step output must be deterministic JSON-compatible data") from error
    return output


def enforce_zero_data():
    install_zero_data_guard()
    assert_no_file_io()
    return True


def harmonise_state(state_log):
    previous_known_step = -1
    seen = set()
    for index, entry in enumerate(state_log):
        if not isinstance(entry, (list, tuple)) or len(entry) != 3:
            raise ValueError("state entries must be (step_name, output, verified) triples")
        name, output, verified = entry
        if not isinstance(name, str) or not name or not isinstance(verified, bool):
            raise ValueError("state entry has an invalid step name or verification flag")
        if name in seen:
            raise ValueError(f"duplicate supervised step: {name}")
        seen.add(name)
        stabilise_step(name, output)
        if name in _KNOWN_STEPS:
            position = _KNOWN_STEPS.index(name)
            if position <= previous_known_step:
                raise HarmonyDriftError("supervised state does not follow burn → ignite → residue")
            previous_known_step = position
        if not verified and index != len(state_log) - 1:
            raise HarmonyDriftError("supervised execution continued after a failed step")
    return True


_sentinel_reference = None


def verify_sentinel(sentinel):
    global _sentinel_reference
    if not isinstance(sentinel, str) or len(sentinel) != 12:
        return False
    try:
        int(sentinel, 16)
    except ValueError:
        return False
    if _sentinel_reference is None:
        _sentinel_reference = sentinel
    return sentinel == _sentinel_reference


class Stabiliser(HarmonyStabilizer):
    def record_step(self, name, output, verified):
        stabilise_step(name, output)
        return super().record_step(name, output, verified)
