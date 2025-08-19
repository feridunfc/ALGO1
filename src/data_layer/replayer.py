
from __future__ import annotations
import pandas as pd
from schemas.events import Event

class DataReplayer:
    def __init__(self, df: pd.DataFrame, source: str = "replayer"):
        self.df = df.sort_values("timestamp")

    def run_sync(self, bus):
        for _, row in self.df.iterrows():
            bar = {"t": row["timestamp"].isoformat(), "o": float(row["open"]), "h": float(row["high"]), "l": float(row["low"]), "c": float(row["close"]), "v": float(row["volume"])}
            ev = Event.create("MARKET_DATA", "replayer", {"symbol": row["symbol"], "bar": bar})
            bus.publish("MARKET_DATA", ev.asdict())
