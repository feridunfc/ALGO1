import time

class PerformanceTracker:
    def __init__(self):
        self.metrics = {
            "latency": {"target": "<100ms", "current": None},
            "throughput": {"target": ">1000 events/s", "current": None},
            "backtest_speed": {"target": "10k bars/s", "current": None},
        }
        self._tic = None
        self._events = 0
        self._start = time.time()

    def tic(self):
        self._tic = time.perf_counter()

    def toc_latency(self):
        if self._tic is None:
            return None
        ms = (time.perf_counter() - self._tic) * 1000.0
        self.metrics["latency"]["current"] = ms
        return ms

    def count_event(self, n: int = 1):
        self._events += n
        elapsed = time.time() - self._start
        if elapsed > 0:
            self.metrics["throughput"]["current"] = self._events / elapsed

    def snapshot(self):
        return self.metrics
