
import numpy as np
import pandas as pd
from engines.strategy_base import BaseStrategy

class HybridV1Strategy(BaseStrategy):
    name = "hybrid_v1"
    def __init__(self, weights: dict | None = None):
        self.w = {"ma": 0.6, "rsi": 0.2, "context": 0.2}
        if weights: self.w.update(weights)
    def predict(self, f: pd.DataFrame) -> pd.Series:
        ma_sig = np.tanh((f["sma20"] - f["sma50"]) / (f["close"].rolling(50).std() + 1e-9))
        rsi_sig = ((f["rsi14"] - 50) / 50.0).clip(-1, 1)
        ctx = (f["regime_score"] * (1 - f["anomaly_score"])).clip(-1, 1)
        raw = self.w["ma"]*ma_sig + self.w["rsi"]*rsi_sig + self.w["context"]*ctx
        return pd.Series(np.clip(raw, -1, 1), index=f.index, name="signal")
