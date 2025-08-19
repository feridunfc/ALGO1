# src/core/ai_wrappers.py
from __future__ import annotations
from typing import Dict, Any
import pandas as pd

# Mevcut ML fonksiyonlarını tek noktadan dışa veren “wrap”:
from .strategies import (
    rf_classifier, svm_classifier, regression_rf, xgb_classifier, hybrid_ensemble
)

# İstersen burada gerçek “sınıf wrapper”ları da yazabilirsin:
class FnWrapper:
    def __init__(self, fn_name: str, params: Dict[str, Any] | None = None):
        self.fn = {
            "rf_classifier": rf_classifier,
            "svm_classifier": svm_classifier,
            "regression_rf": regression_rf,
            "xgb_classifier": xgb_classifier,
            "hybrid_ensemble": hybrid_ensemble,
        }[fn_name]
        self.params = params or {}
    def generate_signals(self, df: pd.DataFrame):
        return self.fn(df, self.params)

# Kayıt defteri (UI/Optuna bu isimleri görsün diye):
ALL_STRATEGIES: Dict[str, Any] = {
    "rf_classifier": rf_classifier,        # fonksiyon
    "svm_classifier": svm_classifier,      # fonksiyon
    "regression_rf": regression_rf,        # fonksiyon
    "xgb_classifier": xgb_classifier,      # fonksiyon
    "hybrid_ensemble": hybrid_ensemble,    # fonksiyon
    # alternatif: sınıf arıyorsan
    # "rf_classifier_cls": lambda p: FnWrapper("rf_classifier", p),
}
