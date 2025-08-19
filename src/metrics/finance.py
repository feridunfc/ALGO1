# src/metrics/finance.py
import numpy as np
import pandas as pd

class SharpeRatio:
    def __call__(self, res) -> float:
        eq = getattr(res, "equity_curve", None)
        if eq is None or len(eq) < 2: return 0.0
        rets = eq.pct_change().dropna()
        if rets.std(ddof=0) == 0: return 0.0
        return float(np.sqrt(252) * rets.mean() / (rets.std(ddof=0) + 1e-12))

class MaxDrawdown:
    def __call__(self, res) -> float:
        eq = getattr(res, "equity_curve", None)
        if eq is None or len(eq) < 2: return 0.0
        roll_max = eq.cummax()
        dd = (eq / roll_max) - 1.0
        return float(dd.min())

class WinRate:
    def __call__(self, res) -> float:
        # placeholder: if res has trades with pnl attribute
        trades = getattr(res, "trades", None)
        if trades is None or len(trades) == 0: return 0.0
        wins = sum(1 for t in trades if getattr(t, "pnl", 0.0) > 0)
        return float(wins / len(trades))

class TurnoverCalculator:
    def __call__(self, res) -> float:
        pos = getattr(res, "positions", None)
        if pos is None or len(pos) < 2: return 0.0
        return float(np.abs(pos.diff().fillna(0)).sum() / len(pos))

class MetricAggregator:
    def __init__(self, metrics):
        self.metrics = metrics
    def compute(self, res):
        out = {}
        for m in self.metrics:
            name = m.__class__.__name__.lower()
            out[name] = float(m(res))
        return out
