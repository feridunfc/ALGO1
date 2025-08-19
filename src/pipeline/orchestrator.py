from __future__ import annotations
import pandas as pd
from typing import Dict, Any
from data.loader import load_ohlcv, normalize_ohlcv
from features.feature_pipeline import build_features, build_target
from core.strategies.ai_unified import AIUnifiedStrategy
from backtesting.adapter import run_backtest_adapter

def _cfg_get(cfg, path: str, default):
    cur = cfg
    for part in path.split("."):
        cur = getattr(cur, part, None) if hasattr(cur, part) else cur.get(part) if isinstance(cur, dict) else None
        if cur is None:
            return default
    return cur

def run_pipeline(strategy: str, params: Dict[str, Any], cfg) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """Used by UI: loads data -> features -> signals -> backtest -> returns (df, info)

    strategy: 'ai_unified' or others (future)
    """
    symbol = _cfg_get(cfg, "data.symbol", "BTC-USD")
    source = _cfg_get(cfg, "data.source", "yfinance")
    interval = _cfg_get(cfg, "data.interval", "1d")
    start = _cfg_get(cfg, "data.start", None)
    end = _cfg_get(cfg, "data.end", None)

    df = load_ohlcv(source=source, symbol=symbol, start=str(start) if start else None, end=str(end) if end else None, interval=interval)
    dfn = normalize_ohlcv(df)

    # Features/target
    feats = build_features(dfn)
    y = build_target(df)

    # Align & cut to recent overlap
    common = feats.index.intersection(y.index).intersection(df.index)
    feats, y, df = feats.loc[common], y.loc[common], df.loc[common]

    # Strategy selection
    if strategy == "ai_unified":
        model_name = params.get("model_name", "random_forest")
        threshold = float(params.get("threshold", 0.5))
        strat = AIUnifiedStrategy(model_name=model_name, threshold=threshold)
        # Vectorized simple split
        signals = strat.fit_predict_vectorized(feats, y)
    else:
        raise KeyError(f"Unknown strategy: {strategy}")

    info = run_backtest_adapter(df, signals,
                                initial_cash=float(_cfg_get(cfg, "bt.initial_cash", 100_000.0)),
                                commission_bps=int(_cfg_get(cfg, "fees.commission_bps", 5)),
                                slippage_bps=int(_cfg_get(cfg, "fees.slippage_bps", 5)))
    return df, info