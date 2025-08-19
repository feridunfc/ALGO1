# hybrid_1_xgb_shap.py
# pip install xgboost shap scikit-learn

from dataclasses import dataclass

try:
    import xgboost as xgb
except Exception as e:
    xgb = None
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
import numpy as np
from module_10_shap_explainer import explain_trading_model

@dataclass
class XGBConfig:
    n_estimators: int = 300
    max_depth: int = 4
    learning_rate: float = 0.05
    subsample: float = 0.9
    colsample_bytree: float = 0.9

def train_xgb_with_shap(X, y, config: XGBConfig = XGBConfig()):
    if xgb is None:
        raise ImportError("xgboost is not installed.")
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    model = xgb.XGBClassifier(
        n_estimators=config.n_estimators,
        max_depth=config.max_depth,
        learning_rate=config.learning_rate,
        subsample=config.subsample,
        colsample_bytree=config.colsample_bytree,
        n_jobs=4,
        eval_metric='logloss'
    )
    model.fit(Xtr, ytr)
    preds = model.predict(Xte)
    proba = model.predict_proba(Xte)[:,1] if len(set(y))==2 else None
    acc = accuracy_score(yte, preds)
    auc = roc_auc_score(yte, proba) if proba is not None else None
    shap_values = explain_trading_model(model, Xte[:200])
    return model, dict(accuracy=acc, auc=auc), shap_values

if __name__ == "__main__":
    from sklearn.datasets import make_classification
    X, y = make_classification(n_samples=1500, n_features=25, random_state=3)
    model, metrics, shap_vals = train_xgb_with_shap(X, y)
    print("XGB metrics:", metrics)
