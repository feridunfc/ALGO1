
from dataclasses import dataclass
from enum import IntEnum
import pandas as pd

class SignalDirection(IntEnum):
    SHORT = -1
    HOLD = 0
    LONG = 1

@dataclass
class StrategySignalGenerated:
    source: str
    symbol: str
    signal: pd.Series
