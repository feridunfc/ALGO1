
import os, sys, json, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from pipeline.orchestrator import run_pipeline

def test_orchestrator_creates_outputs(tmp_dir="/mnt/data/phase7_out"):
    os.makedirs(tmp_dir, exist_ok=True)
    cfg_path = os.path.join(tmp_dir, "config.json")
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump({
            "data": {"source":"synthetic", "bars": 400, "symbol":"BTC-USD", "freq":"T"},
            "risk": {"max_drawdown_pct": 0.10, "max_pos_per_symbol_pct": 0.30},
            "ems": {"algo":"TWAP", "bars_per_parent": 4},
            "strategy": {"ma_fast": 10, "ma_slow": 30, "bb_window": 20, "bb_k": 2.0},
            "out_dir": tmp_dir,
            "title": "Phase7+8 Orchestrator Run"
        }, f, indent=2)
    res = run_pipeline(cfg_path)
    # files exist
    assert os.path.exists(os.path.join(tmp_dir, "report.md"))
    assert os.path.exists(os.path.join(tmp_dir, "metrics.txt"))
    # sanity: equity curve not empty
    assert len(res["equity"]) > 10
