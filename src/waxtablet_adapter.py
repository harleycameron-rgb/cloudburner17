import json

if __package__:
    from .admission import evaluate_submission
    from .orchestrator import Orchestrator
    from .waxtablet_bridge import waxtablet_bridge
else:
    from admission import evaluate_submission
    from orchestrator import Orchestrator
    from waxtablet_bridge import waxtablet_bridge


class WaxtabletAdapter:
    """Translate in-memory Waxtablet actions into engine operations."""

    def __init__(self):
        self.orch = Orchestrator()

    def initialise(self):
        result = self.orch.initialise()
        return {"waxtablet_runtime": "initialised", "engine": result}

    def handle(self, payload):
        if not isinstance(payload, dict):
            return {"error": "payload must be an object"}

        action = payload.get("action")
        if action == "run":
            return self.orch.run_full_engine()
        if action == "benchmark":
            data = payload.get("data")
            if data is None:
                return {"error": "benchmark requires data"}
            self.orch.load_benchmark_data(data)
            return self.orch.run_benchmark()
        if action == "harmonic":
            return self.orch.harmonic_cycle()
        if action == "bridge":
            try:
                return waxtablet_bridge(payload.get("vector"))
            except (TypeError, ValueError) as error:
                return {"error": str(error)}
        if action == "admission":
            try:
                return evaluate_submission(payload.get("submission"))
            except (TypeError, ValueError) as error:
                return {"error": str(error)}
        return {"error": f"unknown action '{action}'"}

    def encode(self, response):
        return json.dumps(
            response,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
