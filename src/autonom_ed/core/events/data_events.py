from dataclasses import dataclass
from datetime import datetime
from .base import BaseEvent

@dataclass
class DataFetchRequested(BaseEvent):
    symbol: str
    start: str
    end: str
    interval: str

@dataclass
class CleanedDataReady(BaseEvent):
    symbol: str
    df: "object"  # pandas DataFrame

@dataclass
class BarDataEvent(BaseEvent):
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
