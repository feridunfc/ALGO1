
from __future__ import annotations
import time, threading

class TokenBucket:
    def __init__(self, rate_per_sec: float, capacity: float | None = None):
        self.rate = float(rate_per_sec)
        self.capacity = float(capacity if capacity is not None else rate_per_sec)
        self.tokens = self.capacity
        self.timestamp = time.time()
        self.lock = threading.Lock()

    def take(self, cost: float = 1.0) -> bool:
        with self.lock:
            now = time.time()
            elapsed = now - self.timestamp
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.timestamp = now
            if self.tokens >= cost:
                self.tokens -= cost
                return True
            return False
