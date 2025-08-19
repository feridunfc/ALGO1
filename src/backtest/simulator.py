
from __future__ import annotations
from typing import Dict, Any, Optional
import pandas as pd
from infra.event_bus import EventBus
from data_layer.replayer import DataReplayer
from core.pipeline import CorePipeline
from backtest.broker_virtual import VirtualBroker
from backtest.metrics import summarize

def run_backtest(df: pd.DataFrame, feature_spec: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    bus = EventBus()
    pipe = CorePipeline(bus, feature_spec=feature_spec, max_history=600)
    broker = VirtualBroker(start_cash=100_000.0, fee_bps=5.0, slippage_bps=5.0, exec_mode="next_open")
    broker.subscribe(bus)
    DataReplayer(df, source="backtest").run_sync(bus)
    eq = broker.equity_curve()
    trades = broker.trades_frame()
    # frequency infer (approx): use pandas infer for equity timestamps
    freq = "D"
    if len(eq) > 1:
        delta = (eq["t"].iloc[1] - eq["t"].iloc[0]).total_seconds()
        if delta <= 60:
            freq = "M"
        elif delta <= 3600:
            freq = "H"
        else:
            freq = "D"
    stats = summarize(eq["equity"], trades, freq=freq)
    return {"equity": eq, "trades": trades, "stats": stats}
