
import pandas as pd
import numpy as np

REQUIRED_COLS = ["open", "high", "low", "close"]

class InvalidDataError(Exception):
    pass

class OHLCValidator:
    def validate(self, df: pd.DataFrame) -> bool:
        # columns
        cols = [c.lower() for c in df.columns]
        if not all(col in cols for col in REQUIRED_COLS):
            return False
        # normalize case
        m = {c: c.lower() for c in df.columns}
        dfn = df.rename(columns=m).copy()
        # types
        for c in REQUIRED_COLS:
            if not np.issubdtype(dfn[c].dtype, np.number):
                return False
        # ranges
        ok = (dfn["high"] >= dfn["low"]) & (dfn["close"] <= dfn["high"]) & (dfn["close"] >= dfn["low"])
        if not ok.all():
            return False
        # index monotonic
        if not isinstance(dfn.index, (pd.DatetimeIndex, pd.Index)):
            return False
        if isinstance(dfn.index, pd.DatetimeIndex) and not dfn.index.is_monotonic_increasing:
            return False
        return True

class VolumeSpikeDetector:
    def __init__(self, window: int = 20, spike_mult: float = 10.0):
        self.window = window
        self.spike_mult = spike_mult

    def validate(self, df: pd.DataFrame) -> bool:
        if "volume" not in [c.lower() for c in df.columns]:
            return True  # no volume to validate
        vol = df.rename(columns={c: c.lower() for c in df.columns})["volume"].astype("float64")
        ma = vol.rolling(self.window, min_periods=self.window//2).mean()
        spikes = vol > (ma * self.spike_mult)
        if spikes.any():
            df.attrs["volume_spike_count"] = int(spikes.sum())
        return True

def normalize_ohlc_columns(df: pd.DataFrame) -> pd.DataFrame:
    m = {c: c.lower() for c in df.columns}
    dfn = df.rename(columns=m).copy()
    return dfn

def ensure_timezone(df: pd.DataFrame, tz: str = "UTC") -> pd.DataFrame:
    if isinstance(df.index, pd.DatetimeIndex):
        if df.index.tz is None:
            df.index = df.index.tz_localize(tz)
        else:
            df.index = df.index.tz_convert(tz)
    return df

def validate_ohlc(df: pd.DataFrame) -> None:
    if not OHLCValidator().validate(df):
        raise InvalidDataError("OHLC validation failed.")
