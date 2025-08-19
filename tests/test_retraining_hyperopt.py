
import os, sys, pandas as pd, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from mlops.retraining import retrain_and_save

def test_retrain_saves_params(tmp_dir="/mnt/data/phase8_out"):
    os.makedirs(tmp_dir, exist_ok=True)
    # synthetic data
    prices = list(range(1, 200)) + [120]*60 + list(range(110, 160))
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=len(prices), freq="T", tz="UTC"),
        "symbol":["BTC-USD"]*len(prices),
        "open":prices, "high":[p+1 for p in prices], "low":[max(0,p-1) for p in prices], "close":prices, "volume":[100]*len(prices)
    })
    best_params, best_stats = retrain_and_save(df, tmp_dir, grid={"ma_fast":[10,20], "ma_slow":[30,50], "bb_window":[20], "bb_k":[2.0, 2.5]})
    path = os.path.join(tmp_dir, "best_strategy_params.json")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    assert "params" in obj and "stats" in obj
