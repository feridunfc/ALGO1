
import os, sys, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from data_layer.normalizer import normalize_ohlcv

def test_yf_multiindex():
    idx = pd.to_datetime(['2023-01-02','2023-01-03'])
    cols = pd.MultiIndex.from_product([['Open','High','Low','Close','Adj Close','Volume'], ['AAA']])
    data = [[100,105,99,101,101,1000],[101,106,100,102,102,1100]]
    raw = pd.DataFrame(data, index=idx, columns=cols)
    out = normalize_ohlcv(raw, source="yfinance")
    assert set(["timestamp","symbol","open","high","low","close","volume"]).issubset(out.columns)
    assert out["symbol"].iloc[0] == "aaa" or out["symbol"].iloc[0] == "AAA".lower()
    assert len(out) == 2

def test_ccxt_list():
    rows = [
        [1672617600000, 100,105,99,101,1000],
        [1672704000000, 101,106,100,102,1100],
    ]
    out = normalize_ohlcv(rows, source="ccxt", symbol="BTC-USD")
    assert "symbol" in out.columns and out["symbol"].iloc[0] == "BTC-USD"
    assert str(out["timestamp"].dt.tz.iloc[0]) == "UTC"
    assert float(out["close"].iloc[-1]) == 102.0
