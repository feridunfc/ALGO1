
import pytest
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

# robust imports
try:
    from src.core.event_bus import EnhancedEventBus
    from src.core.payload_store import PayloadStore
    from src.core.backtest_engine import EventDrivenBacktestEngine
except Exception:
    from core.event_bus import EnhancedEventBus
    from core.payload_store import PayloadStore
    from core.backtest_engine import EventDrivenBacktestEngine

@pytest.mark.asyncio
async def test_backtest_engine_runs_minimal():
    bus = EnhancedEventBus()
    with tempfile.TemporaryDirectory() as d:
        store = PayloadStore(Path(d))
        engine = EventDrivenBacktestEngine(bus, store, {
            "initial_capital": 100000,
            "commission": 0.001,
            "slippage": 0.0005,
            "timeframe": "1d"
        })
        # minimal 3-row dataset
        dates = pd.date_range(end=datetime.utcnow(), periods=3, freq='D')
        df = pd.DataFrame({
            "timestamp": dates,
            "symbol": ["AAPL"]*3,
            "open": [100.0, 101.0, 102.0],
            "high": [101.0, 102.0, 103.0],
            "low":  [ 99.0, 100.0, 101.0],
            "close":[100.5, 101.5, 102.5],
            "volume":[1000, 1100, 1200],
        })
        await engine.run(df, speed=100.0)  # should not raise
