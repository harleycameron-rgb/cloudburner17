if __package__:
    from .orchestrator import Orchestrator
else:
    from orchestrator import Orchestrator


class AgentInterface:
    """In-process interface for initializing and running CLOUDBURNER17."""

    def __init__(self):
        self.orch = Orchestrator()

    def initialise(self):
        return self.orch.initialise()

    def run(self):
        return self.orch.run_full_engine()

    def load_benchmark(self, data):
        self.orch.load_benchmark_data(data)
        return {"benchmark_loaded": True}

    def run_benchmark(self):
        return self.orch.run_benchmark()
