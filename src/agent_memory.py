from collections import deque


class AgentMemory:
    """A transient FIFO buffer held only in process memory."""

    def __init__(self):
        self.buffer = deque()

    def push(self, item):
        self.buffer.append(item)

    def pull(self):
        return self.buffer.popleft() if self.buffer else None

    def clear(self):
        self.buffer.clear()
