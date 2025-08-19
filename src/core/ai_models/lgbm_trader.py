# module_6_lgbm_trader.py
# pip install lightgbm scikit-learn

import numpy as np
from dataclasses import dataclass

try:
    import lightgbm as lgb
except Exception as e:
    lgb = None
from sklearn.metrics import roc_auc_score, accuracy_score
from sklearn.model_selection import train_test_split

@dataclass
class LGBMTraderConfig:
    num_leaves: int = 31
    learning_rate: float = 0.05
    n_estimators: int = 300

class LGBMTrader:
    def __init__(self, config: LGBMTraderConfig = LGBMTraderConfig()):
        if lgb is None:
            raise ImportError("lightgbm is not installed.")
        self.cfg = config
        self.model = lgb.LGBMClassifier(
            num_leaves=self.cfg.num_leaves,
            learning_rate=self.cfg.learning_rate,
            n_estimators=self.cfg.n_estimators
        )

    def fit(self, X, y, test_size=0.2, random_state=42):
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)
        self.model.fit(Xtr, ytr, eval_set=[(Xte, yte)], verbose=False)
        preds = self.model.predict(Xte)
        proba = self.model.predict_proba(Xte)[:,1] if len(set(y))==2 else None
        acc = accuracy_score(yte, preds)
        auc = roc_auc_score(yte, proba) if proba is not None else None
        return dict(accuracy=acc, auc=auc)

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        return self.model.predict_proba(X)

    def feature_importance(self):
        return self.model.feature_importances_
    
if __name__ == "__main__":
    from sklearn.datasets import make_classification
    X, y = make_classification(n_samples=2000, n_features=20, random_state=7)
    trader = LGBMTrader()
    metrics = trader.fit(X, y)
    print("Validation metrics:", metrics)
    print("Feature importances:", trader.feature_importance())
