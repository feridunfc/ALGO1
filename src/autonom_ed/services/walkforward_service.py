from datetime import datetime
import pandas as pd
from ..core.bus.event_bus import event_bus
from ..core.events.backtest_events import BacktestRequested

class WalkForwardService:
    def __init__(self, n_splits=5, embargo_days=5):
        self.bus = event_bus
        self.n_splits = int(n_splits)
        self.embargo_days = int(embargo_days)

    def run(self, symbol: str, start: str, end: str, interval: str, strategy_name: str):
        # Simple date splits by index after fetching once (for simplicity use BacktestingService DataProvider directly here)
        # In a more purist setup, emit a data fetch and listen for CleanedDataReady.
        from ..engines.data_provider_engine import DataProviderEngine
        eng = DataProviderEngine()
        df = eng.fetch(symbol, start, end, interval)
        idx = df.index
        folds = []
        # time series folds
        cuts = pd.Series(range(len(idx)))
        split_points = [int(len(idx)*(i/(self.n_splits+1))) for i in range(1,self.n_splits+1)]
        last = 0
        for sp in split_points:
            train_end = sp - self.embargo_days if sp - self.embargo_days > last else sp
            trains = (idx[last:train_end][0], idx[train_end-1] if train_end>last else idx[train_end])
            tests = (idx[sp], idx[min(sp+self.embargo_days, len(idx)-1)])
            folds.append((trains, tests))
            last = sp
        # publish backtests per fold (using test window per simplicity)
        for (tr_s, tr_e), (te_s, te_e) in folds:
            self.bus.publish(BacktestRequested(
                source="WalkForwardService", timestamp=datetime.utcnow(),
                symbol=symbol, start=str(te_s.date()), end=str(te_e.date()),
                interval=interval, strategy_name=strategy_name
            ))
