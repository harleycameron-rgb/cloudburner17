import math
from common.receipt import Receipt, burn

class LaunchTower:
    def __init__(self, name):
        self.name = name

    def generate_receipt(self, params):
        return Receipt(self.name, params).export()

    def commit_geometry(self, receipt):
        s = receipt["timestamp"] % 3.14159
        return {
            "origin": self.name,
            "vector": [
                round(math.sin(s), 6),
                round(math.cos(s), 6),
                round(math.sin(s * 0.5), 6)
            ],
            "curvature": round(abs(math.sin(s) * math.cos(s)) * 0.1137, 6)
        }

    def ignite(self, params):
        # 1. Generate receipt
        receipt = self.generate_receipt(params)

        # 2. Commit geometry
        geometry = self.commit_geometry(receipt)

        # 3. Hand geometry to Tentacled Sphere (return it upward)
        handoff = {
            "tower": self.name,
            "geometry": geometry,
            "receipt": receipt
        }

        # 4. Burn receipt
        burned = burn(receipt)

        # 5. Shutdown
        return {
            "handoff": handoff,
            "burn_event": burned,
            "shutdown": f"{self.name} tower offline"
        }
