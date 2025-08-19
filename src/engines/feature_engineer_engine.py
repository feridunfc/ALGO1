
import numpy as np
import pandas as pd
from detectors.market_regime_detector import compute_market_regime
from detectors.anomaly_detector import compute_anomaly

class FeatureEngineerEngine:
    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or {}

    def build_features(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy().sort_index()
        out["ret"] = out["close"].pct_change()
        out["vol20"] = out["ret"].rolling(20).std()
        out["sma20"] = out["close"].rolling(20).mean()
        out["sma50"] = out["close"].rolling(50).mean()
        out["rsi14"] = self._rsi(out["close"], 14)
        out["regime_score"] = compute_market_regime(out, "close")
        out["anomaly_score"] = compute_anomaly(out, "close")
        return out.dropna()

    @staticmethod
    def _rsi(prices: pd.Series, n: int = 14) -> pd.Series:
        delta = prices.diff()
        up = (delta.clip(lower=0)).ewm(alpha=1/n, adjust=False).mean()
        down = (-delta.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
        rs = up / (down + 1e-9)
        rsi = 100 - 100 / (1 + rs)
        return rsi.rename("rsi")
