
import os, sys, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from data_layer.indicators import sma, rsi

def test_sma_rsi():
    s = pd.Series([1,2,3,4,5,6])
    out = sma(s, 3)
    assert out.iloc[-1] == 5.0
    r = rsi(s, 3)
    assert r.iloc[-1] > 50.0  # yükselen seride RSI > 50
