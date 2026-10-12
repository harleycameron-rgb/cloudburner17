import hashlib
import time
import json

class Receipt:
    def __init__(self, tower_name, payload):
        self.tower_name = tower_name
        self.timestamp = time.time()
        self.payload = payload
        self.commitment = self._generate_commitment()

    def _generate_commitment(self):
        raw = f"{self.tower_name}:{self.timestamp}:{json.dumps(self.payload)}"
        return hashlib.sha512(raw.encode()).hexdigest()

    def export(self):
        return {
            "tower": self.tower_name,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "commitment": self.commitment
        }

def burn(receipt):
    # Burning = zeroing identity + returning to origin
    return {
        "tower": receipt["tower"],
        "burned_at": time.time(),
        "status": "receipt_burned",
        "commitment_zeroed": True
    }
