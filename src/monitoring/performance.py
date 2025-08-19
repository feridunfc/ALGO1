
import time

class PerformanceTracker:
    def __init__(self):
        self.metrics = {
            "latency_ms": None,
            "throughput_eps": None,
            "backtest_speed_bps": None,
        }
        self._t0 = None
        self._events = 0

    def tic(self):
        self._t0 = time.perf_counter()
        self._events = 0

    def bump(self, n: int = 1):
        self._events += n

    def toc(self):
        if self._t0 is None:
            return
        dt = time.perf_counter() - self._t0
        self.metrics["latency_ms"] = (dt * 1000.0)
        self.metrics["throughput_eps"] = (self._events / dt) if dt > 0 else None
        return self.metrics
