
# services/data_service.py
import logging
import pandas as pd
from typing import Optional
from core.bus.event_bus import event_bus
from core.events.data_events import DataFetchRequested, CleanedDataReady
from utils.yf_helpers import normalize_yf, synthetic_walk

logger = logging.getLogger("DataService")

class DataService:
    """Listens for DataFetchRequested and emits CleanedDataReady."""
    def __init__(self) -> None:
        self.bus = event_bus
        self.bus.subscribe(DataFetchRequested, self.on_request)
        logger.info("DataService ready.")

    def _fetch_yf(self, symbol: str, start: Optional[str], end: Optional[str], interval: str) -> pd.DataFrame:
        try:
            import yfinance as yf
        except Exception:
            logger.warning("yfinance not available, using synthetic walk.")
            return synthetic_walk(symbol)

        kwargs = dict(period=None, start=start, end=end, interval=interval, progress=False, auto_adjust=True)
        df = yf.download(symbol, **kwargs)
        if df is None or df.empty:
            logger.warning("yfinance returned no data; falling back to synthetic.")
            return synthetic_walk(symbol)
        return normalize_yf(df)

    def on_request(self, event: DataFetchRequested) -> None:
        logger.info("Fetching data for %s [%s-%s, %s]", event.symbol, event.start, event.end, event.interval)
        df = self._fetch_yf(event.symbol, event.start, event.end, event.interval)
        if df.empty:
            logger.error("No data fetched for %s", event.symbol)
            return
        self.bus.publish(CleanedDataReady(source="DataService", symbol=event.symbol, df=df))
