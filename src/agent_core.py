import sys

sys.dont_write_bytecode = True

if __package__:
    from .autonomy import autonomous_cycle, invariant_loop, self_verify
    from .pipeline import create_supervisor
    from .stabiliser import (
        enforce_zero_data,
        harmonise_state,
        stabilise_step,
        verify_sentinel,
    )
else:
    from autonomy import autonomous_cycle, invariant_loop, self_verify
    from pipeline import create_supervisor
    from stabiliser import (
        enforce_zero_data,
        harmonise_state,
        stabilise_step,
        verify_sentinel,
    )


class CloudburnerAgent:
    def __init__(self):
        self.supervisor = create_supervisor()
        self.state = []
        self.sentinel = None
        self._initialised = False

    def _prepare_cycle(self):
        if self._initialised and self.supervisor.state_log:
            self.supervisor = create_supervisor()
            self._initialised = False

    def initialise(self):
        enforce_zero_data()
        if self._initialised:
            return
        self._initialised = True

    def execute(self):
        self._prepare_cycle()
        self.initialise()
        results = []
        for step in ("burn", "ignite", "residue"):
            result = self.supervisor.run(step, "y")
            if result.get("status") != "completed":
                raise RuntimeError(f"supervised step failed: {step}")
            stabilise_step(step, result["output"])
            results.append(result)

        self.state = list(self.supervisor.state_log)
        harmonise_state(self.state)
        enforce_zero_data()
        self.sentinel = self.supervisor.residue()["sentinel"]
        if not verify_sentinel(self.sentinel):
            raise RuntimeError("sentinel is not reproducible")
        return {"status": "complete", "results": results, "sentinel": self.sentinel}

    def autonomous_mode(self):
        self._prepare_cycle()
        self.initialise()
        cycle = autonomous_cycle(self.supervisor)
        self.state = list(self.supervisor.state_log)
        self.sentinel = cycle["residue"]["sentinel"]
        reference = invariant_loop()
        verified = self_verify()
        if (
            reference["residue"]["sentinel"] != self.sentinel
            or not verified
            or not verify_sentinel(self.sentinel)
        ):
            raise RuntimeError("autonomous invariant verification failed")
        return {"status": "complete", "sentinel": self.sentinel, "verified": True}


def main():
    agent = CloudburnerAgent()
    print(agent.autonomous_mode())


if __name__ == "__main__":
    main()
