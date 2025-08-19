import pandas as pd
from ..base_strategy import BaseStrategy

def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0).rolling(period).mean()
    down = -delta.clip(upper=0).rolling(period).mean()
    rs = up / (down + 1e-12)
    return 100 - (100 / (1 + rs))

class RSIStrategy(BaseStrategy):
    def __init__(self, params=None):
        super().__init__("rsi", params)
        self.period = int(self.params.get("period", 14))
        self.buy = float(self.params.get("buy", 30))
        self.sell = float(self.params.get("sell", 70))

    def predict(self, df: pd.DataFrame) -> pd.Series:
        rsi = _rsi(df["close"].astype(float), self.period)
        long = (rsi < self.buy).astype(int)
        short = (rsi > self.sell).astype(int) * -1
        sig = (long + short).replace({2:1, -2:-1}).shift(1).fillna(0.0)
        sig.name = "signal"
        return sig
