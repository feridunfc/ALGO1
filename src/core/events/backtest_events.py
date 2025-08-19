
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict
import pandas as pd
from .base_event import BaseEvent

@dataclass(frozen=True)
class BacktestStarted(BaseEvent):
    strategy_name: str = ""
    params: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class BacktestCompleted(BaseEvent):
    strategy_name: str = ""
    results: Dict[str, Any] = field(default_factory=dict)
    equity_curve: pd.Series = field(default_factory=pd.Series)
