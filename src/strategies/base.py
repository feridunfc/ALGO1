from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

import numpy as np
import pandas as pd

# Pydantic varsa parametre şeması için kullan; yoksa sade bir sınıf ile devam et
try:
    from pydantic import BaseModel
except Exception:  # pydantic yoksa
    class BaseModel:  # type: ignore
        pass


class StrategyParameters(BaseModel):  # UI formu/registry için ortak şema
    """Hafif/kural tabanlı strateji parametreleri için temel şema."""
    threshold: float = 0.5  # to_signals için varsayılan


class Strategy(ABC):
    """
    Hafif/kural tabanlı stratejiler için temel sınıf.
    Registry/UI bu sınıftan türeyenleri de strateji sayacak.
    """
    name: str = "Strategy"
    display_name: str = "Strategy"
    family: str = "conventional"
    is_strategy: bool = True       # discovery için işaret
    trainable: bool = False

    def __init__(self, params: Optional[StrategyParameters] = None):
        self.params = params or StrategyParameters()

    # Opsiyonel; çoğu kural tabanlı strateji fit gerektirmez
    def fit(self, df: pd.DataFrame) -> None:
        return None

    def retrain(self, df: pd.DataFrame) -> None:
        return None

    @abstractmethod
    def predict_proba(self, df: pd.DataFrame) -> pd.Series:
        """
        0..1 arasında yukarı yön ihtimali (veya tercih edilen pozitif sınıf) döndür.
        İsterseniz bunun yerine generate_signals'ı override edebilirsiniz.
        """
        raise NotImplementedError

    def generate_signals(self, df: pd.DataFrame, threshold: Optional[float] = None) -> pd.Series:
        """Varsayılan köprü: predict_proba -> to_signals."""
        proba = self.predict_proba(df)
        thr = threshold if threshold is not None else float(getattr(self.params, "threshold", 0.5))
        return self.to_signals(proba, threshold=thr)

    def to_signals(self, proba: pd.Series, threshold: float = 0.5) -> pd.Series:
        """Proba -> {-1,0,1} sinyale çevirir; NaN'leri 0 kabul eder."""
        s = pd.Series(0, index=proba.index, name="signal", dtype=int)
        p = proba.copy()
        # NaN koruması
        if p.dtype.kind in "biu":
            p = p.astype(float)
        p = p.fillna(0.5)
        s.loc[p > threshold] = 1
        s.loc[p < (1.0 - threshold)] = -1
        return s
