
import pandas as pd
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    def __init__(self, name: str):
        self.name = name

    def train(self, df: pd.DataFrame):
        return self

    @abstractmethod
    def signal_for_row(self, row: pd.Series) -> float:
        """Return signal strength in [-1,1] for this row."""
        ...

    def __repr__(self):
        return f"<Strategy {self.name}>"
