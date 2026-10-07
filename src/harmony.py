import math
from collections.abc import Mapping
from numbers import Real

if __package__:
    from .stabiliser import stabilise_step
else:
    from stabiliser import stabilise_step


def align_modules(modules):
    if not isinstance(modules, Mapping):
        raise TypeError("modules must map module names to outputs")
    aligned = {}
    for name in sorted(modules):
        aligned[name] = stabilise_step(name, modules[name])
    return aligned


def unify_lambdas(lambda_values):
    values = tuple(lambda_values)
    if not values or any(
        isinstance(value, bool)
        or not isinstance(value, Real)
        or not math.isfinite(value)
        or value < 0
        for value in values
    ):
        raise ValueError("lambda values must be a non-empty finite non-negative vector")
    total = math.fsum(values)
    if total <= 0:
        raise ValueError("lambda vector must have a positive total")
    return [value / total for value in values]


def smooth_residue(residue):
    if isinstance(residue, (list, tuple)) and len(residue) == 2:
        value, tag = residue
        if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
            raise ValueError("residue value must be a finite number")
        if not isinstance(tag, str):
            raise ValueError("residue tag must be a string")
        return round(float(value), 12), tag
    if isinstance(residue, bool) or not isinstance(residue, Real) or not math.isfinite(residue):
        raise ValueError("residue must be a finite number or (number, tag) pair")
    return round(float(residue), 12)


def main():
    assert unify_lambdas([0.5, 0.7]) == unify_lambdas([0.5, 0.7])
    assert smooth_residue((6.0, "mapping-definition-6")) == (
        6.0,
        "mapping-definition-6",
    )
    print("harmony checks passed")


if __name__ == "__main__":
    main()
