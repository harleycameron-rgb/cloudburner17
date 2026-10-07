from dataclasses import dataclass
from typing import Callable, Dict, Any

@dataclass
class Step:
    name: str
    action: Callable[[], Any]
    verify: Callable[[Any], bool]

class Supervisor:
    def __init__(self):
        self.steps: Dict[str, Step] = {}
        self.state_log = []
        self.sentinel = None

    def add_step(self, name: str, action: Callable[[], Any], verify: Callable[[Any], bool]):
        self.steps[name] = Step(name, action, verify)

    def run(self, name: str, decision: str):
        if name not in self.steps:
            return {"error": f"Unknown step '{name}'"}
        if decision.lower() != "y":
            return {"status": "skipped", "step": name}
        step = self.steps[name]
        output = step.action()
        ok = step.verify(output)
        self.state_log.append((name, output, ok))
        if not ok:
            return {"status": "failed", "step": name, "output": output}
        return {"status": "completed", "step": name, "output": output}

    def residue(self):
        import hashlib
        blob = str(self.state_log).encode()
        self.sentinel = hashlib.sha256(blob).hexdigest()[:12]
        return {"sentinel": self.sentinel, "log": self.state_log}
