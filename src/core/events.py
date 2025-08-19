# src/core/events.py
from pydantic import BaseModel
import pandas as pd
from typing import Literal

class DataReadyEvent(BaseModel):
    kind: Literal["DataReadyEvent"] = "DataReadyEvent"
    symbol: str
    frame: pd.DataFrame  # OHLCV; index tz-aware, monotonic, unique
