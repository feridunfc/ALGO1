
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List
import pandas as pd
from .base_event import BaseEvent

@dataclass(frozen=True)
class DataFetchRequested(BaseEvent):
    symbols: List[str] = field(default_factory=list)
    timeframe: str = "1d"
    lookback_days: int = 365

@dataclass(frozen=True)
class DataReadyEvent(BaseEvent):
    symbol: str = ""
    data: pd.DataFrame = field(default_factory=pd.DataFrame)

@dataclass(frozen=True)
class DataFetchFailed(BaseEvent):
    symbol: str = ""
    error: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
