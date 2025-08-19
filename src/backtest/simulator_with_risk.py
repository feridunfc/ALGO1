
from __future__ import annotations
from typing import Dict, Any, Optional
import pandas as pd
from infra.event_bus import EventBus
from data_layer.replayer import DataReplayer
from core.pipeline import CorePipeline
from backtest.broker_virtual import VirtualBroker
from backtest.metrics import summarize
from risk.gate import RiskGate
from risk.limits import RiskLimits

def run_backtest_with_risk(df: pd.DataFrame, feature_spec: Optional[Dict[str, Any]] = None, limits: Optional[RiskLimits] = None) -> Dict[str, Any]:
    bus = EventBus()
    broker = VirtualBroker(start_cash=100_000.0, fee_bps=5.0, slippage_bps=5.0, exec_mode="next_open", bus=bus)
    broker.subscribe(bus)
    pipe = CorePipeline(bus, feature_spec=feature_spec, max_history=600)
    gate = RiskGate(bus, broker_snapshot_fn=broker.snapshot, limits=limits)

    DataReplayer(df, source="backtest").run_sync(bus)
    eq = broker.equity_curve()
    trades = broker.trades_frame()
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
