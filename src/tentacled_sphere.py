import json
import math
import time
from numbers import Real


class TentacledSphere:
    """Generate an in-memory geometry state for eight named tentacles."""

    def __init__(self, seed=1.0, delta=0.1137):
        self.seed = self._finite_number(seed, "seed")
        self.delta = self._finite_number(delta, "delta")
        self.tentacles = {
            "TAP_CONVEX": self.geom_convex,
            "SURFACE_CONCAVE": self.geom_concave,
            "GAIN_PSYCHOSOCIAL": self.geom_gain,
            "HABITATAT_DOMAIN": self.geom_habitat,
            "TIME_CHRONO": self.geom_time,
            "SPACE_CHRONO": self.geom_space,
            "SCANROOT_LINEAGE": self.geom_lineage,
            "SCANDOCZERO_AUDIT": self.geom_audit,
        }

    @staticmethod
    def _finite_number(value, name):
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError(f"{name} must be a finite real number")
        value = float(value)
        if not math.isfinite(value):
            raise ValueError(f"{name} must be a finite real number")
        return value

    def geom_convex(self, s):
        return self._pack("convex", math.sin(s), math.cos(s), math.sin(s * 0.5))

    def geom_concave(self, s):
        return self._pack(
            "concave", math.sin(s * 0.337), math.cos(s * 0.771), math.sin(s * 0.1137)
        )

    def geom_gain(self, s):
        return self._pack(
            "psychosocial",
            math.sin(s * 0.1137),
            math.cos(s * 0.3371),
            math.sin(s * 0.7711),
        )

    def geom_habitat(self, s):
        return self._pack(
            "domain",
            math.sin(s * 0.8869),
            math.cos(s * 0.6065),
            math.sin(s * 0.7170),
        )

    def geom_time(self, s):
        return self._pack("chrono_time", s * 0.1137, s * 0.3371, s * 0.7711)

    def geom_space(self, s):
        return self._pack("chrono_space", math.sin(s), math.sin(s * 2), math.sin(s * 3))

    def geom_lineage(self, s):
        return self._pack("lineage", math.cos(s), math.cos(s * 2), math.cos(s * 3))

    def geom_audit(self, s):
        return self._pack(
            "audit",
            math.sin(s * 0.1137),
            math.cos(s * 0.3371),
            math.sin(s * 0.7711) * math.cos(s * 0.8869),
        )

    @staticmethod
    def _pack(label, x, y, z):
        if not all(math.isfinite(value) for value in (x, y, z)):
            raise ValueError("geometry vectors must contain finite values")
        curvature = abs(x * y * z) * 0.1137
        if not math.isfinite(curvature):
            raise ValueError("geometry curvature must be finite")
        return {
            "label": label,
            "vector": [round(x, 6), round(y, 6), round(z, 6)],
            "curvature": round(curvature, 6),
            "timestamp": time.time(),
        }

    def actuate(self):
        state = self.seed
        output = {}
        for name, geometry in self.tentacles.items():
            if not math.isfinite(state):
                raise ValueError("seed and delta produce a non-finite geometry state")
            try:
                output[name] = geometry(state)
            except (OverflowError, ValueError) as error:
                raise ValueError(
                    "seed and delta must produce finite geometry values"
                ) from error
            state += self.delta
        return output

    def export_json(self):
        """Serialize the current state in memory without writing a file."""
        return json.dumps(self.actuate(), indent=4, allow_nan=False)
