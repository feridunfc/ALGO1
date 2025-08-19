
from __future__ import annotations
import os, json
import pandas as pd
from typing import Dict, Any, Tuple
from mlops.hyperopt import grid_search_params
from risk.limits import RiskLimits

def retrain_and_save(df: pd.DataFrame, out_dir: str, grid: Dict[str, list] | None = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    os.makedirs(out_dir, exist_ok=True)
    limits = RiskLimits(max_drawdown_pct=0.10, max_pos_per_symbol_pct=0.30)
    grid = grid or {
        "ma_fast":[10,20],
        "ma_slow":[50,100],
        "bb_window":[20],
        "bb_k":[2.0, 2.5]
    }
    best_params, best_stats = grid_search_params(df, grid, limits)
    # persist a tiny "model config"
    with open(os.path.join(out_dir, "best_strategy_params.json"), "w", encoding="utf-8") as f:
        json.dump({"params": best_params, "stats": best_stats}, f, indent=2)
    return best_params, best_stats
