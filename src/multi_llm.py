class LLMAdapter:
    def __init__(self, name, pos, weight, f, r, ports):
        self.name = name
        self.pos = pos
        self.weight = weight
        self.f = f
        self.r = r
        self.ports = ports

    def to_module(self):
        return {"name": self.name, "ports": self.ports}
