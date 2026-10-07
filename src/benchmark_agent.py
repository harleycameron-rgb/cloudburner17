import hashlib
import json
import math
from collections.abc import Mapping
from numbers import Real


def _records(data):
    if hasattr(data, "to_dict"):
        try:
            data = data.to_dict(orient="records")
        except TypeError:
            data = data.to_dict()
    if isinstance(data, Mapping):
        if not data:
            return []
        columns = list(data.values())
        if not all(isinstance(column, (list, tuple)) for column in columns):
            raise TypeError("benchmark mappings must contain column sequences")
        lengths = {len(column) for column in columns}
        if len(lengths) > 1:
            raise ValueError("benchmark columns must have matching lengths")
        keys = list(data)
        return [
            {key: data[key][index] for key in keys}
            for index in range(next(iter(lengths), 0))
        ]
    if isinstance(data, (list, tuple)) and all(
        isinstance(row, Mapping) for row in data
    ):
        return [dict(row) for row in data]
    raise TypeError("benchmark data must be records or a dataframe-like object")


def _vector(values, name):
    if not isinstance(values, (list, tuple)) or len(values) != 3:
        raise ValueError(f"{name} must contain exactly three values")
    if any(isinstance(value, bool) or not isinstance(value, Real) for value in values):
        raise ValueError(f"{name} values must be real numbers")
    result = tuple(float(value) for value in values)
    if not all(math.isfinite(value) for value in result):
        raise ValueError(f"{name} values must be finite")
    return result


def _norm(vector):
    return math.sqrt(math.fsum(value * value for value in vector))


def _normalise(vector, name):
    magnitude = _norm(vector)
    if magnitude == 0 or not math.isfinite(magnitude):
        raise ValueError(f"{name} must have a finite, non-zero norm")
    return tuple(value / magnitude for value in vector)


def phi(values):
    return _normalise(_vector(values, "x_params"), "x_params")


def A(parameters):
    values = _vector(parameters, "p_params")
    return tuple(
        tuple(values[row] if row == column else 0.0 for column in range(3))
        for row in range(3)
    )


def G(state):
    return tuple(state[:2])


def F(state, control):
    return (state[0] * control[0], state[1] * control[1], 0.0)


def parabolic_step_down(state, control, control_offset=0.7, t=1.0):
    if len(state) != len(control):
        raise ValueError("state and control dimensions must match")
    if not 0.0 <= t <= 1.0 or not math.isfinite(t):
        raise ValueError("t must be finite and within [0, 1]")
    control_point = tuple(
        value + control_offset * (target - value)
        for value, target in zip(state, control)
    )
    return tuple(
        (1.0 - t) ** 2 * value
        + 2.0 * t * (1.0 - t) * point
        + t**2 * target
        for value, point, target in zip(state, control_point, control)
    )


def _uniform_stream(seed):
    counter = 0
    while True:
        digest = hashlib.sha256(seed + counter.to_bytes(8, "big")).digest()
        counter += 1
        for offset in range(0, len(digest), 8):
            integer = int.from_bytes(digest[offset : offset + 8], "big")
            yield (integer + 0.5) / (2**64)


def _deterministic_controls(row, samples):
    seed = json.dumps(
        {"x_params": row["x_params"], "p_params": row["p_params"]},
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    uniforms = _uniform_stream(seed)
    for _ in range(samples):
        u1, u2, u3, u4 = (next(uniforms) for _ in range(4))
        radius_xy = math.sqrt(-2.0 * math.log(u1))
        theta_xy = 2.0 * math.pi * u2
        radius_z = math.sqrt(-2.0 * math.log(u3))
        theta_z = 2.0 * math.pi * u4
        direction = (
            radius_xy * math.cos(theta_xy),
            radius_xy * math.sin(theta_xy),
            radius_z * math.cos(theta_z),
        )
        direction = _normalise(direction, "sampled direction")
        yield tuple(component * next(uniforms) for component in direction)


def compute_benchmark_row(row, samples=100):
    if not isinstance(row, Mapping):
        raise TypeError("benchmark row must be a mapping")
    if not isinstance(samples, int) or isinstance(samples, bool) or samples <= 0:
        raise ValueError("samples must be a positive integer")
    if "x_params" not in row or "p_params" not in row:
        raise ValueError("benchmark row requires x_params and p_params")

    x = _vector(row["x_params"], "x_params")
    p = _vector(row["p_params"], "p_params")
    state = phi(x)
    matrix = A(p)
    projected = []
    for column in range(3):
        projected.append(
            math.fsum(
                ((1.0 if row_index == column else 0.0) - state[row_index] * state[column])
                * matrix[row_index][column]
                for row_index in range(3)
            )
        )
    perturbed = _normalise(
        tuple(value + delta for value, delta in zip(state, projected)),
        "perturbed state",
    )

    surface_distance = math.acos(
        min(1.0, max(-1.0, math.fsum(a * b for a, b in zip(state, perturbed))))
    )
    state_control = (state[0], state[1], 0.0)
    perturbed_control = (perturbed[0], perturbed[1], 0.0)
    state_surface = parabolic_step_down(state, state_control)
    perturbed_surface = parabolic_step_down(perturbed, perturbed_control)
    state_core = G(state)
    perturbed_core = G(perturbed)
    core_distance = _norm(
        tuple(b - a for a, b in zip(state_core, perturbed_core))
    )

    flow_squared = []
    for control in _deterministic_controls(
        {"x_params": x, "p_params": p}, samples
    ):
        state_flow = F(state_core, control)
        perturbed_flow = F(perturbed_core, control)
        flow_squared.append(
            math.fsum(
                (b - a) ** 2 for a, b in zip(state_flow, perturbed_flow)
            )
        )
    flow_distance = math.sqrt(math.fsum(flow_squared) / samples)

    return {
        "D_surface": surface_distance,
        "D_core": core_distance,
        "D_flow": flow_distance,
        "s0": list(state),
        "sp": list(perturbed),
        "z0": list(state_core),
        "zp": list(perturbed_core),
        "s0_surf": list(state_surface),
        "sp_surf": list(perturbed_surface),
    }


class BenchmarkAgent:
    """Evaluate records in memory with deterministic geometric benchmark metrics."""

    def __init__(self, data, samples=100):
        self._records = _records(data)
        self.samples = samples
        if not isinstance(samples, int) or isinstance(samples, bool) or samples <= 0:
            raise ValueError("samples must be a positive integer")
        self.results = None

    def run(self):
        self.results = [
            compute_benchmark_row(record, self.samples)
            if "x_params" in record or "p_params" in record
            else dict(record)
            for record in self._records
        ]
        return [dict(result) for result in self.results]

    def worst_case_leakage(self):
        results = self.results if self.results is not None else self.run()
        values = []
        for result in results:
            value = result.get("D_core", result.get("leakage", 0.0))
            if (
                isinstance(value, bool)
                or not isinstance(value, Real)
                or not math.isfinite(value)
                or value < 0
            ):
                raise ValueError(
                    "benchmark leakage values must be finite and non-negative"
                )
            values.append(float(value))
        return max(values, default=0.0)

    def structural_control(self, x, x_prime):
        return _norm(
            tuple(
                b - a
                for a, b in zip(G(phi(x)), G(phi(x_prime)))
            )
        )
