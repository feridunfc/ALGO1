from abc import ABC, abstractmethod
import pandas as pd

class Strategy(ABC):
    name: str = "Strategy"
    def fit(self, df: pd.DataFrame) -> None: ...
    def retrain(self, df: pd.DataFrame) -> None: ...
    @abstractmethod
    def predict_proba(self, df: pd.DataFrame) -> pd.Series: ...
    def to_signals(self, proba: pd.Series, threshold: float = 0.5) -> pd.Series:
        sig = proba.copy()*0
        sig[proba > threshold] = 1
        sig[proba < (1.0 - threshold)] = -1
        return sig
