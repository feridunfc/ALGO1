
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from pipeline.orchestrator import run_pipeline

def test_live_stub_flow(tmp_dir="/mnt/data/phase9_live_stub"):
    os.makedirs(tmp_dir, exist_ok=True)
    cfg_path = os.path.join(tmp_dir, "config.json")
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump({
            "mode": "live_stub",
            "data": { "source":"synthetic", "bars": 120, "symbol":"BTC-USD", "freq":"T" },
            "risk": { "max_drawdown_pct": 0.15, "max_pos_per_symbol_pct": 0.30 },
            "ems": { "algo":"TWAP", "bars_per_parent": 3 },
            "strategy": { "ma_fast": 10, "ma_slow": 30, "bb_window": 20, "bb_k": 2.0 },
            "out_dir": tmp_dir,
            "title": "Live Stub Demo",
            "exchange": "BINANCE"
        }, f, indent=2)
    res = run_pipeline(cfg_path)
    assert len(res["equity"]) > 10
    assert os.path.exists(os.path.join(tmp_dir, "report.md"))
    assert os.path.exists(res["metrics_path"])
