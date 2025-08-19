
import numpy as np
import pandas as pd

def safe_division(a, b, default=0.0):
    try:
        return a / b if b not in (0, 0.0, None) else default
    except Exception:
        return default

def format_currency(x: float, unit: str = "$"):
    return f"{unit}{x:,.2f}"

class TechnicalAnalysis:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def rsi(self, period: int = 14) -> pd.Series:
        delta = self.df["close"].diff()
        up = delta.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
        down = -delta.clip(upper=0).ewm(alpha=1/period, adjust=False).mean()
        rs = up / (down.replace(0, np.nan))
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.fillna(method="bfill").fillna(50)
        return rsi

    def macd(self, fast: int = 12, slow: int = 26, signal: int = 9):
        ema_fast = self.df["close"].ewm(span=fast, adjust=False).mean()
        ema_slow = self.df["close"].ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        return macd, signal_line
