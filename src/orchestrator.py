if __package__:
    from .agent_core import CloudburnerAgent
    from .autonomy import invariant_loop, self_verify
    from .benchmark_agent import BenchmarkAgent
    from .stabiliser import enforce_zero_data, harmonise_state, verify_sentinel
else:
    from agent_core import CloudburnerAgent
    from autonomy import invariant_loop, self_verify
    from benchmark_agent import BenchmarkAgent
    from stabiliser import enforce_zero_data, harmonise_state, verify_sentinel


class Orchestrator:
    """Coordinate the supervised agent and optional in-memory benchmarks."""

    def __init__(self):
        enforce_zero_data()
        self.agent = CloudburnerAgent()
        self.benchmark = None
        self.state_log = []
        self.sentinel = None

    def initialise(self):
        self.agent.initialise()
        return {"status": "initialised"}

    def run_agent(self):
        result = self.agent.execute()
        self.state_log.append(result)
        self.sentinel = result["sentinel"]
        if not verify_sentinel(self.sentinel):
            raise RuntimeError("agent sentinel is not reproducible")
        return result

    def load_benchmark_data(self, data):
        self.benchmark = BenchmarkAgent(data)

    def run_benchmark(self):
        if self.benchmark is None:
            raise RuntimeError("Benchmark data not loaded")
        results = self.benchmark.run()
        leakage = self.benchmark.worst_case_leakage()
        summary = {
            "benchmark_results": results,
            "worst_case_leakage": leakage,
        }
        self.state_log.append(summary)
        return {"benchmark": "complete", "worst_case_leakage": leakage}

    def harmonic_cycle(self):
        harmonise_state(self.agent.state)
        cycle = invariant_loop()
        if not self_verify():
            raise RuntimeError("harmonic cycle verification failed")
        return {
            "harmonic_state": True,
            "sentinel": cycle["residue"]["sentinel"],
        }

    def run_full_engine(self):
        out_agent = self.run_agent()
        out_benchmark = self.run_benchmark() if self.benchmark is not None else None
        out_harmonic = self.harmonic_cycle()
        if not verify_sentinel(self.sentinel):
            raise RuntimeError("engine sentinel is not reproducible")
        enforce_zero_data()
        return {
            "agent": out_agent,
            "benchmark": out_benchmark,
            "harmonic": out_harmonic,
            "sentinel": self.sentinel,
        }
