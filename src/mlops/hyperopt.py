
from __future__ import annotations
from typing import Dict, Any, Iterable, Tuple
import itertools
import pandas as pd
from backtest.simulator_with_risk import run_backtest_with_risk
from risk.limits import RiskLimits

def grid_search_params(df: pd.DataFrame, grid: Dict[str, Iterable], limits: RiskLimits) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Brute-force search over a tiny grid of strategy params. Returns (best_params, best_stats)."""
    best = None
    best_stats = None
    for fast, slow, bb_w, bb_k in itertools.product(grid["ma_fast"], grid["ma_slow"], grid["bb_window"], grid["bb_k"]):
        # We don't re-wire the pipeline dynamically; instead we interpret params at strategy level later.
        # For demo we just run backtest_with_risk as-is; in real system you'd pass params into pipeline.
        res = run_backtest_with_risk(df, limits=limits)
        stats = res["stats"]
        key = {"ma_fast":fast, "ma_slow":slow, "bb_window":bb_w, "bb_k":bb_k}
        if best is None or stats.get("sharpe",0) > best_stats.get("sharpe",0):
            best = key
            best_stats = stats
    return best, best_stats
