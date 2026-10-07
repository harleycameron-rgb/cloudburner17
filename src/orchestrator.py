from agent_core import CloudburnerAgent
from benchmark_agent import BenchmarkAgent
from stabiliser import enforce_zero_data, harmonise_state, verify_sentinel
from harmony import align_modules, unify_lambdas, smooth_residue
from autonomy import autonomous_cycle, invariant_loop, self_verify

import pandas as pd
import numpy as np


class Orchestrator:
    """
    The unified CLOUDBURNER17 orchestration layer.
    Binds Agent Core + Benchmark Agent + Harmony + Autonomy + Stabiliser.
    """

    def __init__(self):
        enforce_zero_data()

        # Primary agent
        self.agent = CloudburnerAgent()

        # Benchmark agent placeholder (data injected later)
        self.benchmark = None

        # Orchestration state
        self.state_log = []
        self.sentinel = None

    # ------------------------------------------------------------
    # INITIALISATION
    # ------------------------------------------------------------

    def initialise(self):
        self.agent.initialise()
        return {"status": "initialised"}

    # ------------------------------------------------------------
    # RUN PRIMARY AGENT
    # ------------------------------------------------------------

    def run_agent(self):
        result = self.agent.execute()
        self.state_log.append(result)
        self.sentinel = result["sentinel"]
        verify_sentinel(self.sentinel)
        return result

    # ------------------------------------------------------------
    # RUN BENCHMARK AGENT
    # ------------------------------------------------------------

    def load_benchmark_data(self, df):
        """Inject benchmark dataframe."""
        self.benchmark = BenchmarkAgent(df)

    def run_benchmark(self):
        if self.benchmark is None:
            raise RuntimeError("Benchmark data not loaded")

        results = self.benchmark.run()
        leakage = self.benchmark.worst_case_leakage()

        self.state_log.append({
            "benchmark_results": results.to_dict(orient="records"),
            "worst_case_leakage": leakage
        })

        return {
            "benchmark": "complete",
            "worst_case_leakage": leakage
        }

    # ------------------------------------------------------------
    # HARMONIC CYCLE
    # ------------------------------------------------------------

    def harmonic_cycle(self):
        """
        Runs a deterministic harmonic cycle across all agents.
        """
        autonomous_cycle(self.agent.supervisor)
        invariant_loop()
        self_verify()

        harmonised = harmonise_state(self.state_log)
        return {"harmonic_state": harmonised}

    # ------------------------------------------------------------
    # FULL ENGINE EXECUTION
    # ------------------------------------------------------------

    def run_full_engine(self):
        """
        Executes the entire CLOUDBURNER17 engine:
        - Agent Core
        - Benchmark Agent (if loaded)
        - Harmonic Cycle
        - Sentinel verification
        """
        out_agent = self.run_agent()

        out_benchmark = None
        if self.benchmark:
            out_benchmark = self.run_benchmark()

        out_harmonic = self.harmonic_cycle()

        verify_sentinel(self.sentinel)

        return {
            "agent": out_agent,
            "benchmark": out_benchmark,
            "harmonic": out_harmonic,
            "sentinel": self.sentinel
        }
