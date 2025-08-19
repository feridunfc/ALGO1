# src/core/data_normalizer.py
import pandas as pd, numpy as np
from typing import Optional
from .config import NormalizationConfig
from .events import DataReadyEvent

REQUIRED_COLS = ["open", "high", "low", "close", "volume"]

class DataNormalizer:
    """Industry-grade normalizer with strict OHLCV + index invariants."""
    def __init__(self, config: Optional[NormalizationConfig] = None, strict_mode: bool = True):
        self.config = config or NormalizationConfig()
        self.strict_mode = strict_mode

    def fit_transform(self, data: pd.DataFrame, symbol: Optional[str] = None) -> pd.DataFrame:
        self._validate_input_schema(data)
        df = data.copy()

        # tz enforcement
        if df.index.tz is None:
            df.index = df.index.tz_localize(self.config.tz)
        else:
            df.index = df.index.tz_convert(self.config.tz)

        # optional NaN handling (only in non-strict mode)
        if not self.strict_mode and df.isnull().any().any():
            df = self._apply_nan_policy(df)

        # optional winsorization via z-score clip
        if self.config.clip_outliers_z:
            ohlc = ["open","high","low","close"]
            z = (df[ohlc] - df[ohlc].mean()) / df[ohlc].std(ddof=0)
            z = z.clip(lower=-self.config.clip_outliers_z, upper=self.config.clip_outliers_z)
            df.loc[:, ohlc] = z

        # scaling
        df = self._scale(df)

        self._validate_output_schema(df)

        if symbol:
            _ = DataReadyEvent(symbol=symbol, frame=df)
        return df

    # internals
    def _validate_input_schema(self, data: pd.DataFrame) -> None:
        missing = [c for c in REQUIRED_COLS if c not in data.columns]
        if missing:
            if self.strict_mode: raise ValueError(f"Missing columns: {missing}")
        if not isinstance(data.index, pd.DatetimeIndex):
            raise TypeError("Index must be DatetimeIndex")
        if self.config.ensure_monotonic and not data.index.is_monotonic_increasing:
            raise ValueError("Index must be monotonically increasing")
        if self.config.ensure_unique_index and not data.index.is_unique:
            raise ValueError("Index must be unique")
        if self.strict_mode and data.isnull().any().any():
            raise ValueError("NaN values detected in strict mode")

    def _apply_nan_policy(self, df: pd.DataFrame) -> pd.DataFrame:
        policy = self.config.nan_policy
        if policy == "drop":
            return df.dropna()
        if policy == "ffill":
            return df.ffill().dropna()
        if policy == "bfill":
            return df.bfill().dropna()
        if policy == "interp":
            return df.interpolate(method="time").ffill().bfill()
        if policy == "fill_value":
            fv = 0.0 if self.config.fill_value is None else float(self.config.fill_value)
            return df.fillna(fv)
        return df

    def _scale(self, df: pd.DataFrame) -> pd.DataFrame:
        s = self.config.scaler
        if s == "none":
            return df
        cols = ["open","high","low","close","volume"]
        x = df[cols].astype(float)
        if s == "zscore":
            mu, sigma = x.mean(), x.std(ddof=0).replace(0.0, np.nan)
            x = (x - mu) / sigma
        elif s == "minmax":
            mn, mx = x.min(), x.max()
            denom = (mx - mn).replace(0.0, np.nan)
            x = (x - mn) / denom
        elif s == "robust":
            q1, q3 = x.quantile(0.25), x.quantile(0.75)
            denom = (q3 - q1).replace(0.0, np.nan)
            x = (x - q1) / denom
        df.loc[:, cols] = x
        return df

    def _validate_output_schema(self, df: pd.DataFrame) -> None:
        if list(df.columns) != REQUIRED_COLS:
            raise ValueError("Output columns must be exactly OHLCV")
        if df.index.tz is None:
            raise ValueError("Index must be tz-aware")
        if not df.index.is_monotonic_increasing:
            raise ValueError("Index must be monotonically increasing")
        if not df.index.is_unique:
            raise ValueError("Index must be unique")
