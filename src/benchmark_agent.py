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


class BenchmarkAgent:
    """Evaluate in-memory benchmark records without external state or artifacts."""

    def __init__(self, data):
        self._records = _records(data)

    def run(self):
        return [dict(record) for record in self._records]

    def worst_case_leakage(self):
        values = []
        for record in self._records:
            value = record.get("leakage", 0.0)
            if (
                isinstance(value, bool)
                or not isinstance(value, Real)
                or not math.isfinite(value)
                or value < 0
            ):
                raise ValueError("benchmark leakage values must be finite and non-negative")
            values.append(float(value))
        return max(values, default=0.0)
