import time


def runtime_ignition():
    state = {
        "status": "IGNITION_READY",
        "residue": 0,
        "drift": 0,
        "invariant": True,
        "timestamp": time.time_ns() // 1_000_000,
    }
    assert state["invariant"] is True
    return state
