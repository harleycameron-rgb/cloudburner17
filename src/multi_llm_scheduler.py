import math
from collections.abc import Mapping, Sequence
from numbers import Real


def _aligned_values(value, count, name):
    if isinstance(value, Real) and not isinstance(value, bool):
        values = (value,) * count
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        values = tuple(value)
        if len(values) != count:
            raise ValueError(f"{name} must contain exactly {count} values")
    else:
        raise ValueError(f"{name} must be a number or a sequence")
    if any(
        isinstance(item, bool)
        or not isinstance(item, Real)
        or not math.isfinite(item)
        or item < 0
        for item in values
    ):
        raise ValueError(f"{name} values must be finite non-negative numbers")
    return tuple(float(item) for item in values)


def _name(item, kind):
    if isinstance(item, str) and item:
        return item
    if isinstance(item, Mapping):
        name = item.get("name")
    else:
        name = getattr(item, "name", None)
    if not isinstance(name, str) or not name:
        raise ValueError(f"each {kind} must have a non-empty name")
    return name


def schedule_tasks(llms, tasks, lam, times):
    llms = tuple(llms)
    tasks = tuple(tasks)
    if not llms or not tasks:
        raise ValueError("llms and tasks must both be non-empty")

    weights = _aligned_values(lam, len(llms), "lam")
    if not any(weights):
        raise ValueError("lam must contain at least one positive value")
    timings = _aligned_values(times, len(tasks), "times")
    llm_names = tuple(_name(llm, "LLM") for llm in llms)
    task_names = tuple(_name(task, "task") for task in tasks)

    return [
        {
            "llm": llm_names[index % len(llms)],
            "task": task_name,
            "lambda": weights[index % len(llms)],
            "time": timings[index],
        }
        for index, task_name in enumerate(task_names)
    ]
