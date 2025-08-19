# src/anomaly/threshold.py
from typing import Dict, List

import numpy as np

class DynamicThreshold:
    def __init__(self, window_size: int = 100, z_threshold: float = 3.0):
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.history: Dict[str, List[float]] = {}

    def update(self, metric: str, value: float):
        self.history.setdefault(metric, []).append(float(value))
        if len(self.history[metric]) > self.window_size:
            self.history[metric] = self.history[metric][-self.window_size:]

    def check_anomaly(self, metric: str, value: float) -> bool:
        values = self.history.get(metric, [])
        if len(values) < 10:
            return False
        mu = float(np.mean(values))
        sigma = float(np.std(values))
        if sigma == 0:
            return False
        z = abs((float(value) - mu) / sigma)
        return z > self.z_threshold

    def get_thresholds(self) -> Dict[str, Dict[str, float]]:
        out: Dict[str, Dict[str, float]] = {}
        for m, values in self.history.items():
            if len(values) >= 10:
                mu = float(np.mean(values))
                sigma = float(np.std(values))
                out[m] = {"lower": mu - self.z_threshold * sigma, "upper": mu + self.z_threshold * sigma, "mean": mu}
        return out
