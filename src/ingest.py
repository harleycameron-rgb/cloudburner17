import time


def ingest_test_results(results):
    results = list(results)
    return {
        "passed": sum(1 for result in results if result["ok"]),
        "failed": sum(1 for result in results if not result["ok"]),
        "vector": [
            {
                "name": result["name"],
                "ok": result["ok"],
                "timestamp": time.time_ns() // 1_000_000,
            }
            for result in results
        ],
        "invariant_pulse": all(result["ok"] for result in results),
    }
