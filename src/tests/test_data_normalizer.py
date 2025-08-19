# src/tests/test_data_normalizer.py
import numpy as np
import pandas as pd

from core.data_normalizer import (
    DataNormalizer,
    FinancialDataNormalizer,
    NormalizationConfig,
    NormalizationMethod,
    NaNPolicy,
)


def _make_df(n=200):
    idx = pd.date_range("2023-01-01", periods=n, freq="D")
    df = pd.DataFrame({
        "feat1": np.linspace(0, 10, n) + np.random.normal(0, 0.5, n),
        "feat2": np.random.lognormal(mean=0.0, sigma=0.5, size=n),
        "open": np.linspace(100, 120, n),
        "close": np.linspace(100, 120, n) + np.random.normal(0, 1.0, n),
    }, index=idx)
    # add some NaNs
    df.iloc[5:8, 0] = np.nan
    return df


def test_zscore_basic():
    df = _make_df()
    cfg = NormalizationConfig(
        method=NormalizationMethod.ZSCORE,
        nan_policy=NaNPolicy.FFILL,
        include_cols=["feat1", "feat2"],
    )
    norm = FinancialDataNormalizer(cfg)
    out = norm.fit_transform(df)
    assert out.shape == df.shape
    assert out[["feat1","feat2"]].isnull().sum().sum() == 0


def test_minmax_clip():
    df = _make_df()
    cfg = NormalizationConfig(
        method=NormalizationMethod.MINMAX,
        nan_policy=NaNPolicy.FFILL,
        include_cols=["feat1"],
        clip_outliers=True,
    )
    norm = DataNormalizer(cfg)
    out = norm.fit_transform(df)
    assert (out["feat1"] >= 0).all() and (out["feat1"] <= 1).all()


def test_rolling_no_lookahead():
    df = _make_df()
    cfg = NormalizationConfig(
        method=NormalizationMethod.ZSCORE,
        nan_policy=NaNPolicy.FFILL,
        include_cols=["feat1", "feat2"],
        rolling_window=30,
    )
    norm = FinancialDataNormalizer(cfg)
    out = norm.transform(df)
    # first 30 rows drop due to rolling
    assert len(out) <= len(df) - 30
    assert out[["feat1","feat2"]].isnull().sum().sum() == 0
