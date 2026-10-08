import time

if __package__:
    from .ingest import ingest_test_results
else:
    from ingest import ingest_test_results


def runtime_ignition(test_results=()):
    ingested = ingest_test_results(test_results)
    state = {
        "status": "IGNITION_READY",
        "residue": ingested["failed"],
        "drift": 1 if ingested["failed"] > 0 else 0,
        "invariant": ingested["invariant_pulse"],
        "vector": ingested["vector"],
        "timestamp": time.time_ns() // 1_000_000,
    }
    assert state["invariant"] is ingested["invariant_pulse"]
    return state
