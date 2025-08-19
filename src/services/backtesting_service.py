from __future__ import annotations
import logging, pandas as pd
from core.event_bus import event_bus
from core.events import BacktestRequested, BacktestCompleted, BarDataEvent
from engines.data_loader import DataLoader
from backtest.walkforward import generate_walkforward_slices

logger = logging.getLogger("BacktestingService")

class BacktestingService:
    def __init__(self):
        self.bus = event_bus
        self.bus.subscribe(BacktestRequested, self._on_request)
        logger.info("BacktestingService ready.")

    def _on_request(self, evt: BacktestRequested):
        df = DataLoader().load_yfinance(evt.symbol, evt.start, evt.end, evt.interval)
        if evt.mode == "full":
            self._replay(df, is_train=False)
        else:
            for tr_idx, te_idx in generate_walkforward_slices(df, evt.wf_train, evt.wf_test):
                self._replay(df.iloc[tr_idx], is_train=True)
                self._replay(df.iloc[te_idx], is_train=False)
        self.bus.publish(BacktestCompleted(source="BacktestingService", symbol=evt.symbol, results={}))

    def _replay(self, df: pd.DataFrame, is_train: bool):
        sym = df["symbol"].iloc[0] if "symbol" in df.columns else ""
        for ts, row in df.iterrows():
            self.bus.publish(BarDataEvent(
                source="BacktestReplay", symbol=sym, timestamp=ts,
                open=float(row["open"]), high=float(row["high"]), low=float(row["low"]),
                close=float(row["close"]), volume=float(row["volume"]), is_train=is_train
            ))
