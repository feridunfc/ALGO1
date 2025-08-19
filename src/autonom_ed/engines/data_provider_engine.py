import pandas as pd
import yfinance as yf

class DataProviderEngine:
    def fetch(self, symbol: str, start: str, end: str, interval: str) -> pd.DataFrame:
        df = yf.download(symbol, start=start, end=end, interval=interval, progress=False)
        if df is None or len(df) == 0:
            raise ValueError("yfinance returned empty data")
        # Normalize columns to lower-case ohlcv
        cols = {c.lower(): c for c in df.columns}
        # For yfinance, columns often 'Open','High', etc., lower them:
        df.columns = [c.lower() for c in df.columns]
        expected = {"open","high","low","close","volume"}
        missing = expected - set(df.columns)
        if missing:
            # yfinance sometimes returns 'adj close' etc; try fix
            if "adj close" in df.columns and "close" not in df.columns:
                df["close"] = df["adj close"]
                missing = expected - set(df.columns)
            if missing:
                raise ValueError(f"yfinance returned unexpected columns: {set(df.columns)}")
        df = df[["open","high","low","close","volume"]].copy()
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        return df
