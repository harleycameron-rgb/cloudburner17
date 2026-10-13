"""Deterministic, in-memory synthetic scores; not physical curvature."""

import math


class SyntheticGeometry:
    def __init__(self, seed=1.0, delta=0.1137):
        self.seed = seed
        self.delta = delta
        self.in_memory = True
        self.functions = [
            self.func_tap,
            self.func_surface,
            self.func_gain,
            self.func_habitatat,
            self.func_time,
            self.func_space,
            self.func_scanroot,
            self.func_scandoczero,
        ]

    def curvature_score(self, x, y, z):
        return round(abs(x*y*z) * 0.1137, 6)

    def func_tap(self, s):
        return self.curvature_score(math.sin(s), math.cos(s), math.sin(s*0.5))

    def func_surface(self, s):
        return self.curvature_score(
            math.sin(s*0.337), math.cos(s*0.771), math.sin(s*0.1137)
        )

    def func_gain(self, s):
        return self.curvature_score(
            math.sin(s*0.1137), math.cos(s*0.3371), math.sin(s*0.7711)
        )

    def func_habitatat(self, s):
        return self.curvature_score(
            math.sin(s*0.8869), math.cos(s*0.6065), math.sin(s*0.7170)
        )

    def func_time(self, s):
        return self.curvature_score(s*0.1137, s*0.3371, s*0.7711)

    def func_space(self, s):
        return self.curvature_score(math.sin(s), math.sin(s*2), math.sin(s*3))

    def func_scanroot(self, s):
        return self.curvature_score(math.cos(s), math.cos(s*2), math.cos(s*3))

    def func_scandoczero(self, s):
        return self.curvature_score(
            math.sin(s*0.1137), math.cos(s*0.3371),
            math.sin(s*0.7711)*math.cos(s*0.8869),
        )

    def run_cycle(self):
        results = {}
        s = self.seed
        for fn in self.functions:
            results[fn.__name__] = fn(s)
            s += self.delta
        return results


GEOMETRY = SyntheticGeometry()
IN_MEMORY_RESULTS = GEOMETRY.run_cycle()

if __name__ == "__main__":
    print(IN_MEMORY_RESULTS)
