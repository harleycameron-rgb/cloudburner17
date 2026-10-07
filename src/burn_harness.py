import math
from collections.abc import Sequence
from numbers import Real


def _finite_vector(values, name, minimum_length):
    if (
        not isinstance(values, Sequence)
        or isinstance(values, (str, bytes))
        or len(values) < minimum_length
        or any(
            isinstance(value, bool)
            or not isinstance(value, Real)
            or not math.isfinite(value)
            for value in values
        )
    ):
        raise ValueError(f"{name} must be a finite numeric sequence")
    return tuple(float(value) for value in values)


def burn_harness(sound, lambda_values, times):
    sound = _finite_vector(sound, "sound", 3)
    lambda_values = _finite_vector(lambda_values, "lambda_values", 1)
    times = _finite_vector(times, "times", 1)
    if len(sound) != len(times):
        raise ValueError("sound and times must have the same length")
    if len(times) < 3:
        raise ValueError("times must contain at least three samples")
    if any(later <= earlier for earlier, later in zip(times, times[1:])):
        raise ValueError("times must be strictly increasing")
    if any(value < 0 for value in lambda_values):
        raise ValueError("lambda_values must be non-negative")

    curvature = []
    for index in range(1, len(sound) - 1):
        left_slope = (sound[index] - sound[index - 1]) / (
            times[index] - times[index - 1]
        )
        right_slope = (sound[index + 1] - sound[index]) / (
            times[index + 1] - times[index]
        )
        curvature.append(
            2 * (right_slope - left_slope) / (times[index + 1] - times[index - 1])
        )

    signal_scale = 1 + math.fsum(abs(value) for value in sound) / len(sound)
    curvature_gain = 1 + math.fsum(abs(value) for value in curvature) / (
        len(curvature) * signal_scale
    )
    return {
        "lambda_updated": [value * curvature_gain for value in lambda_values],
        "curvature_gain": curvature_gain,
    }
