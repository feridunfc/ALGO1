from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict
from enum import Enum, auto

# Try to import production BacktestEngine
try:
    from core.backtest_engine import BacktestEngine, OrderType, OrderDirection, PercentageCommissionModel, VolatilityProportionalSlippage  # type: ignore
    _ENGINE_OK = True
except Exception:
    _ENGINE_OK = False

class _MiniReport:
    def __init__(self, equity: pd.Series):
        self.equity = equity
        self.stats = {
            'sharpe': float(np.nan) if equity.pct_change().std() == 0 else
                (equity.pct_change().mean() / (equity.pct_change().std() + 1e-9)) * np.sqrt(252),
            'max_dd': float(((equity.cummax() - equity) / equity.cummax()).max())
        }

def run_backtest_adapter(price_df: pd.DataFrame, signals: pd.Series, initial_cash: float = 100_000.0,
                         commission_bps: int = 5, slippage_bps: int = 5) -> Dict:
    """Turn -1/0/+1 signals into orders at T+1 and run BacktestEngine.
    If engine is unavailable, fallback to a simple PnL model.
    """
    # Align indices
    sig = signals.reindex(price_df.index).fillna(0).astype(int)
    # Generate orders where signal changes
    change = sig.diff().fillna(sig)
    # Build simple order list: enter/exit on next bar open
    if _ENGINE_OK:
        engine = BacktestEngine(
            price_data={"ASSET": price_df},
            initial_capital=initial_cash,
            commission_model=PercentageCommissionModel(rate=commission_bps/1e4, min_commission=0.0),
            slippage_model=VolatilityProportionalSlippage(base_rate=slippage_bps/1e4)
        )
        # Seed current_date at first index
        engine.current_date = price_df.index[0]
        for t, step in change.items():
            if step == 0:
                continue
            direction = OrderDirection.LONG if sig.loc[t] > 0 else OrderDirection.SHORT if sig.loc[t] < 0 else OrderDirection.FLAT
            qty = max(1, int(initial_cash * 0.001 / max(price_df.loc[t, 'close'], 1e-6)))
            engine.submit_order(symbol="ASSET", direction=direction, quantity=qty, order_type=OrderType.MARKET, strategy="ai_unified")
            engine.current_date = t
        rep = engine.run(price_df.index[0], price_df.index[-1])
        equity = rep.get('portfolio_history', pd.Series(dtype=float))
        stats = rep.get('performance', {})
        return {"equity": equity, "stats": stats}
    else:
        # Fallback: naive returns when in position
        ret = price_df['close'].pct_change().fillna(0.0)
        pnl = (sig.shift(1).fillna(0) * ret)  # position active on next bar
        equity = (1 + pnl).cumprod() * initial_cash
        mini = _MiniReport(equity)
        return {"equity": equity, "stats": mini.stats}