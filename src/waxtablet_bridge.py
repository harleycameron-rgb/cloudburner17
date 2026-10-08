if __package__:
    from .runtime import runtime_ignition
else:
    from runtime import runtime_ignition


def waxtablet_bridge(feed_vector):
    """Validate and route a Waxtablet feed vector through runtime ignition."""
    if not isinstance(feed_vector, list):
        raise TypeError("feed vector must be a list")

    for entry in feed_vector:
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("name"), str)
            or not isinstance(entry.get("ok"), bool)
        ):
            raise TypeError("each feed vector entry must have a string name and boolean ok")

    ignition = runtime_ignition(feed_vector)
    invariant_pulse = bool(feed_vector) and ignition["invariant"]

    return {
        "feed": "ACTIVE" if invariant_pulse else "HALTED",
        "invariantPulse": invariant_pulse,
        "vector": ignition["vector"],
        "ignition": ignition,
    }
