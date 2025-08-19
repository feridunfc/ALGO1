# module_7_tabnet_trader.py
# pip install pytorch-tabnet

import numpy as np
import torch
from pytorch_tabnet.tab_model import TabNetClassifier

class TabNetTrader:
    def __init__(self, lr=2e-2, mask_type='sparsemax'):
        self.model = TabNetClassifier(
            optimizer_fn=torch.optim.Adam,
            optimizer_params=dict(lr=lr),
            scheduler_params={"step_size": 10, "gamma": 0.9},
            scheduler_fn=torch.optim.lr_scheduler.StepLR,
            mask_type=mask_type,
            verbose=0
        )

    def fit(self, X, y, eval_set=None, max_epochs=100, patience=10, batch_size=1024):
        self.model.fit(
            X_train=X, y_train=y,
            eval_set=eval_set if eval_set is not None else [(X, y)],
            max_epochs=max_epochs, patience=patience,
            batch_size=batch_size, eval_metric=['accuracy','auc']
        )
        return self

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        return self.model.predict_proba(X)

    def explain(self, X):
        # Returns masks/attributions
        return self.model.explain(X)

if __name__ == "__main__":
    from sklearn.datasets import make_classification
    X, y = make_classification(n_samples=1000, n_features=16, random_state=42)
    trader = TabNetTrader().fit(X, y)
    print("Pred sample:", trader.predict(X[:10]))
