import hashlib
import json


class HarmonyDriftError(ValueError):
    pass


class HarmonyStabilizer:
    def __init__(self):
        self._expected_steps = ()
        self._position = 0
        self._digest = hashlib.sha256(b"CLOUDBURNER17:harmony:v1").hexdigest()

    def configure_steps(self, names):
        names = tuple(names)
        if self._position and names != self._expected_steps:
            raise HarmonyDriftError("supervised step sequence changed during execution")
        self._expected_steps = names

    def check_next(self, name):
        if self._position >= len(self._expected_steps):
            raise HarmonyDriftError("all supervised steps have already run")
        expected = self._expected_steps[self._position]
        if name != expected:
            raise HarmonyDriftError(
                f"expected supervised step '{expected}', received '{name}'"
            )

    def record_step(self, name, output, verified):
        self.check_next(name)
        payload = json.dumps(
            {"step": name, "output": output, "verified": verified},
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        self._digest = hashlib.sha256(
            f"{self._digest}:{payload}".encode("utf-8")
        ).hexdigest()
        self._position += 1

    @property
    def sentinel(self):
        return self._digest[:12]
