# src/pipeline/normalization.py
from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

import pandas as pd

from core.data_normalizer import (
    DataNormalizer,
    FinancialDataNormalizer,
    NormalizationConfig,
    NormalizationMethod,
    NaNPolicy,
    create_normalizer,
)


def _parse_method(name: str) -> NormalizationMethod:
    m = (name or "zscore").strip().upper()
    return {
        "ZSCORE": NormalizationMethod.ZSCORE,
        "MINMAX": NormalizationMethod.MINMAX,
        "ROBUST": NormalizationMethod.ROBUST,
        "LOG": NormalizationMethod.LOG,
        "QUANTILE": NormalizationMethod.QUANTILE,
    }.get(m, NormalizationMethod.ZSCORE)


def _parse_nan_policy(name: str) -> NaNPolicy:
    p = (name or "ffill").strip().upper()
    return {
        "DROP": NaNPolicy.DROP,
        "FFILL": NaNPolicy.FFILL,
        "BFILL": NaNPolicy.BFILL,
        "INTERPOLATE": NaNPolicy.INTERPOLATE,
        "FILL_WITH": NaNPolicy.FILL_WITH,
    }.get(p, NaNPolicy.FFILL)


def apply_normalization(
    df: pd.DataFrame,
    include_cols: Optional[List[str]] = None,
    exclude_cols: Optional[List[str]] = None,
    method: str = "zscore",
    nan_policy: str = "ffill",
    clip_outliers: bool = True,
    rolling_window: Optional[int] = None,
    kind: str = "financial",
) -> pd.DataFrame:
    """Simple one-shot normalization helper."""
    cfg = NormalizationConfig(
        method=_parse_method(method),
        nan_policy=_parse_nan_policy(nan_policy),
        include_cols=include_cols,
        exclude_cols=exclude_cols,
        clip_outliers=clip_outliers,
        rolling_window=rolling_window,
    )
    norm = create_normalizer(kind, cfg)
    return norm.fit_transform(df) if rolling_window is None else norm.transform(df)


def wf_fit_transform(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    include_cols: Optional[List[str]] = None,
    exclude_cols: Optional[List[str]] = None,
    method: str = "zscore",
    nan_policy: str = "ffill",
    clip_outliers: bool = True,
    kind: str = "financial",
):
    """
    Walk-forward safe fit on train, transform on test with same scaler.
    """
    cfg = NormalizationConfig(
        method=_parse_method(method),
        nan_policy=_parse_nan_policy(nan_policy),
        include_cols=include_cols,
        exclude_cols=exclude_cols,
        clip_outliers=clip_outliers,
        rolling_window=None,
    )
    norm = create_normalizer(kind, cfg)
    Xtr = norm.fit_transform(X_train)
    Xte = norm.transform(X_test)
    return Xtr, Xte, norm
