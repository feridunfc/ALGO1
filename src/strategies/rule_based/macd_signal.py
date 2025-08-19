import pandas as pd
from ..base import Strategy
from ..features import macd

class MACDSignal(Strategy):
    name = "rb_macd"
    def predict_proba(self, df):
        macd_line, signal_line, hist = macd(df["close"])
        p = (macd_line - signal_line).apply(lambda x: 0.75 if x>0 else 0.25)
        return p.fillna(0.5).clip(0,1)
