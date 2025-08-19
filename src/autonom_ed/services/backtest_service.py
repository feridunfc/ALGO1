from datetime import datetime
from ..core.bus.event_bus import event_bus
from ..core.events.backtest_events import BacktestRequested, BacktestCompleted
from ..core.events.data_events import DataFetchRequested, CleanedDataReady, BarDataEvent
from ..engines.data_provider_engine import DataProviderEngine

class BacktestingService:
    def __init__(self):
        self.bus = event_bus
        self.pending = None
        self.df_cache = None
        self.bus.subscribe(BacktestRequested, self.on_request)
        self.bus.subscribe(CleanedDataReady, self.on_data_ready)

    def on_request(self, event: BacktestRequested):
        # trigger data fetch
        self.pending = event
        self.bus.publish(DataFetchRequested(
            source="BacktestingService", timestamp=datetime.utcnow(),
            symbol=event.symbol, start=event.start, end=event.end, interval=event.interval
        ))

    def on_data_ready(self, event: CleanedDataReady):
        if self.pending is None or event.symbol != self.pending.symbol:
            return
        df = event.df
        # replay
        for ts, row in df.iterrows():
            self.bus.publish(BarDataEvent(
                source="BacktestingService", timestamp=ts,
                symbol=self.pending.symbol,
                open=float(row["open"]), high=float(row["high"]),
                low=float(row["low"]), close=float(row["close"]),
                volume=float(row["volume"]),
            ))
        # complete
        self.bus.publish(BacktestCompleted(
            source="BacktestingService", timestamp=datetime.utcnow(),
            symbol=self.pending.symbol, start=self.pending.start,
            end=self.pending.end, interval=self.pending.interval,
            strategy_name=self.pending.strategy_name
        ))
        self.pending = None
