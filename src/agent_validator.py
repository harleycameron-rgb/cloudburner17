if __package__:
    from .stabiliser import verify_sentinel
else:
    from stabiliser import verify_sentinel


class AgentValidator:
    def __init__(self):
        self.last_sentinel = None

    def validate(self, sentinel):
        if not verify_sentinel(sentinel):
            raise ValueError("invalid or non-reproducible sentinel")
        if self.last_sentinel is not None and sentinel != self.last_sentinel:
            raise RuntimeError("sentinel drift detected")
        self.last_sentinel = sentinel
        return True
