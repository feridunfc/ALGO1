
# src/pipeline/backtest_runner.py
from __future__ import annotations

import pandas as pd
from typing import Dict, Any
from core.backtest_engine import BacktestEngine, OrderDirection, OrderType, PercentageCommissionModel, VolatilityProportionalSlippage

def run_simple_backtest(price_data: Dict[str, pd.DataFrame], start: str, end: str) -> Dict[str, Any]:
    """
    Minimal convenience wrapper to run a smoke backtest:
     - Buys first symbol on day 1, holds
     - Sells on last day
    """
    engine = BacktestEngine(
        price_data=price_data,
        initial_capital=100_000.0,
        commission_model=PercentageCommissionModel(0.0005, min_commission=1.0),
        slippage_model=VolatilityProportionalSlippage(0.0003),
        risk_free_rate=0.02,
    )
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)

    # Simple order flow: buy 10 shares of first symbol at T+1 from start, sell near end
    first_sym = next(iter(price_data.keys()))
    engine.submit_order(first_sym, OrderDirection.LONG, quantity=10, order_type=OrderType.MARKET, submission_date=start_ts)
    # schedule another add near mid
    mid = start_ts + (end_ts - start_ts) / 2
    engine.submit_order(first_sym, OrderDirection.LONG, quantity=5, order_type=OrderType.MARKET, submission_date=mid)

    report = engine.run(start_ts, end_ts)
    return report
