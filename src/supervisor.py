from dataclasses import dataclass
from typing import Callable, Dict, Any

if __package__:
    from .harmony import align_modules
    from .stabiliser import HarmonyDriftError, Stabiliser, harmonise_state
    from .zero_data import install_zero_data_guard
else:
    from harmony import align_modules
    from stabiliser import HarmonyDriftError, Stabiliser, harmonise_state
    from zero_data import install_zero_data_guard


@dataclass
class Step:
    name: str
    action: Callable[[], Any]
    verify: Callable[[Any], bool]

class Supervisor:
    def __init__(self):
        install_zero_data_guard()
        self.steps: Dict[str, Step] = {}
        self.state_log = []
        self.sentinel = None
        self.stabilizer = Stabiliser()

    def add_step(self, name: str, action: Callable[[], Any], verify: Callable[[Any], bool]):
        self.steps[name] = Step(name, action, verify)

    def run(self, name: str, decision: str):
        if name not in self.steps:
            return {"error": f"Unknown step '{name}'"}
        if decision.lower() != "y":
            return {"status": "skipped", "step": name}
        if self.state_log and not self.state_log[-1][2]:
            return {"status": "failed", "step": name, "error": "previous step failed"}
        try:
            self.stabilizer.configure_steps(self.steps)
            self.stabilizer.check_next(name)
        except HarmonyDriftError as error:
            return {"status": "failed", "step": name, "error": str(error)}
        step = self.steps[name]
        output = step.action()
        try:
            align_modules({name: output})
        except (TypeError, ValueError) as error:
            return {"status": "failed", "step": name, "error": str(error)}
        ok = step.verify(output)
        try:
            self.stabilizer.record_step(name, output, ok)
        except (HarmonyDriftError, TypeError, ValueError) as error:
            return {"status": "failed", "step": name, "error": str(error)}
        next_state = self.state_log + [(name, output, ok)]
        try:
            harmonise_state(next_state)
        except (HarmonyDriftError, TypeError, ValueError) as error:
            return {"status": "failed", "step": name, "error": str(error)}
        self.state_log = next_state
        if not ok:
            return {"status": "failed", "step": name, "output": output}
        return {"status": "completed", "step": name, "output": output}

    def residue(self):
        self.sentinel = self.stabilizer.sentinel
        return {"sentinel": self.sentinel, "log": self.state_log}
