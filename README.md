
# Backtest Engine Hotfix (v2.9.14)

This package adds an industrial-grade `BacktestEngine` with:
- 1-bar execution delay
- Commission & slippage plug-ins
- Multi-asset portfolio accounting
- Detailed trade log
- Robust performance metrics

## Paths
- `src/core/backtest_engine.py`
- `src/pipeline/backtest_runner.py`
- `src/tests/test_backtest_engine.py`

## Quick start

```python
import pandas as pd
from core.backtest_engine import BacktestEngine, OrderDirection, OrderType, PercentageCommissionModel, VolatilityProportionalSlippage

# Load your OHLCV DataFrames into a dict like {"AAPL": df, "MSFT": df}
prices = {...}

engine = BacktestEngine(
    price_data=prices,
    initial_capital=100_000.0,
    commission_model=PercentageCommissionModel(0.0005, min_commission=1.0),
    slippage_model=VolatilityProportionalSlippage(0.0003),
    risk_free_rate=0.02,
)

# You can submit orders before or during run()
engine.submit_order("AAPL", OrderDirection.LONG, 10, OrderType.MARKET)

report = engine.run(start_date=pd.Timestamp("2022-01-03"), end_date=pd.Timestamp("2022-02-15"))
print(report["performance"])
print(report["trades"].head())
```

## Notes
- LIMIT orders are simulated simply: long fills at `min(limit, open)`, short at `max(limit, open)` on execution bar.
- STOP orders can be added later; this hotfix focuses on stability of the core loop.
- Short selling is supported by allowing negative inventory and mark-to-market of equity: `cash + Σ(qty * close)`.
