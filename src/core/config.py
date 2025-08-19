# src/core/config.py
from dataclasses import dataclass
from typing import Literal, Optional

NaNPolicy = Literal["drop", "ffill", "bfill", "interp", "fill_value"]
Scaler = Literal["none", "zscore", "minmax", "robust"]

@dataclass(frozen=True)
class NormalizationConfig:
    nan_policy: NaNPolicy = "ffill"
    fill_value: Optional[float] = None
    scaler: Scaler = "none"
    clip_outliers_z: Optional[float] = None
    tz: str = "UTC"
    ensure_monotonic: bool = True
    ensure_unique_index: bool = True
