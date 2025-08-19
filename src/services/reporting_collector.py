
import pandas as pd
from dataclasses import dataclass
from typing import Any

# Try to import user's bus/events; fall back to internal stubs
try:
    from core.bus.event_bus import event_bus as default_bus
    from core.events.portfolio_events import PortfolioUpdated
    from core.events.backtest_events import BacktestCompleted
except Exception:
    class SimpleBus:
        def __init__(self):
            self.subs = {}
        def subscribe(self, etype, cb):
            self.subs.setdefault(etype, []).append(cb)
        def publish(self, e):
            for cb in self.subs.get(type(e), []):
                cb(e)
    default_bus = SimpleBus()
    @dataclass
    class PortfolioUpdated:
        source: str
        timestamp: Any
        total_value: float
    @dataclass
    class BacktestCompleted:
        source: str
        asset_name: str
        strategy_name: str

from ..engines.metrics_engine import MetricsEngine

class ReportingCollector:
    def __init__(self, bus=None):
        self.bus = bus or default_bus
        self._equity = []
        self.final_report = None
        self.bus.subscribe(PortfolioUpdated, self.on_portfolio_update)
        self.bus.subscribe(BacktestCompleted, self.on_backtest_complete)

    def on_portfolio_update(self, event: 'PortfolioUpdated'):
        self._equity.append((event.timestamp, event.total_value))

    def on_backtest_complete(self, event: 'BacktestCompleted'):
        if not self._equity:
            self.final_report = {"error": "no equity collected"}
            return
        df = pd.DataFrame(self._equity, columns=["timestamp","equity"]).set_index("timestamp").sort_index()
        # normalize to 1.0 start
        eq = df["equity"] / df["equity"].iloc[0]
        metrics = MetricsEngine.compute_all(eq)
        self.final_report = {"asset": getattr(event, "asset_name", "NA"), "strategy": getattr(event, "strategy_name", "NA"), **metrics}
        self._equity = []
