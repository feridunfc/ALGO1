from __future__ import annotations
import pandas as pd
from typing import Dict, Any, Tuple, Optional, Callable
from experiments.tracking import ExperimentTracker
from backtesting.walk_forward import WalkForwardRunner
from risk.anomaly_bridge import AnomalySentimentSizer

def run_backtest_single(features: pd.DataFrame,
                        prices: pd.Series,
                        strategy_factory,
                        strategy_params: Dict[str, Any],
                        tracker: ExperimentTracker = None,
                        run_name: str = "single_run") -> Dict[str, Any]:
    # Minimal single-run: son segmentte train/test gibi kullanılabilir
    runner = WalkForwardRunner(n_splits=2)
    df, summary = runner.run(features, prices, strategy_factory, strategy_params)
    out = {"folds": df, "summary": summary}
    if tracker:
        info = tracker.start_run(run_name, {"strategy": strategy_factory.__name__, **strategy_params})
        tracker.log_metrics(info, {"mean_sharpe": summary.get("mean_sharpe", 0.0)}, step=0)
        tracker.end_run(info, status="finished")
        out["run_id"] = info.run_id
    return out

def run_walk_forward(features: pd.DataFrame,
                     prices: pd.Series,
                     strategy_factory,
                     strategy_params: Dict[str, Any],
                     n_splits: int = 5,
                     test_size: int = None,
                     tracker: ExperimentTracker = None,
                     run_name: str = "wf_run") -> Dict[str, Any]:
    runner = WalkForwardRunner(n_splits=n_splits, test_size=test_size)
    df, summary = runner.run(features, prices, strategy_factory, strategy_params)
    out = {"folds": df, "summary": summary}
    if tracker:
        info = tracker.start_run(run_name, {"strategy": strategy_factory.__name__, **strategy_params,
                                            "n_splits": n_splits, "test_size": test_size})
        # log per-fold
        for i, row in df.iterrows():
            tracker.log_metrics(info, {"sharpe": row["sharpe"], "maxdd": row["maxdd"]}, step=int(row["fold"]))
        tracker.log_metrics(info, {"mean_sharpe": summary.get("mean_sharpe", 0.0)}, step=999)
        tracker.end_run(info, status="finished")
        out["run_id"] = info.run_id
    return out

def apply_risk_overlays(weights: Dict[str, float],
                        constraints: Optional[Callable[[Dict[str, float]], Dict[str, float]]] = None,
                        anomaly_severity: float = 0.0,
                        sentiment_score: float = 0.0) -> Dict[str, float]:
    # Basic hook: anomaly & sentiment sizer (single-asset avg application example)
    sizer = AnomalySentimentSizer()
    if len(weights) == 0:
        return {}
    avg_w = sum(weights.values()) / max(1, len(weights))
    m = sizer.multiplier(severity=anomaly_severity, sentiment=sentiment_score)
    scaled = {k: v * m for k, v in weights.items()}
    # renorm
    s = sum(abs(x) for x in scaled.values())
    if s > 0:
        scaled = {k: v / s for k, v in scaled.items()}
    # constraints hook
    if constraints:
        scaled = constraints(scaled)
    return scaled
