import numpy as np
import pandas as pd
import logging
from .base_ai_model import BaseAIModel, ModelNotTrainedError, MainConfig

logger = logging.getLogger(__name__)

try:
    from pytorch_tabnet.tab_model import TabNetClassifier

    TABNET_AVAILABLE = True
except ImportError:
    TABNET_AVAILABLE = False


class TabNetModel(BaseAIModel):
    def __init__(self, config: MainConfig, model_params: dict):
        super().__init__(model_name='tabnet', config=config)
        self.model_specific_params = model_params

    def _initialize_model(self, params=None):
        if not TABNET_AVAILABLE: raise ImportError("TabNet için 'pytorch-tabnet' kütüphanesi gerekli.")

        current_params = self.params.copy()
        current_params.update(self.model_specific_params)
        if params: current_params.update(params)

        self.model = TabNetClassifier(
            n_d=current_params.get('n_d', 8),
            n_a=current_params.get('n_a', 8),
            n_steps=current_params.get('n_steps', 3),
            gamma=current_params.get('gamma', 1.3),
            lambda_sparse=current_params.get('lambda_sparse', 1e-4),
            optimizer_params=dict(lr=current_params.get('learning_rate', 2e-2)),
            verbose=0
        )

    def train(self, X_train: pd.DataFrame, y_train: pd.Series, **kwargs):
        self._initialize_model(self.best_params or {})
        X_np, y_np = self._prepare_data(X_train, y_train, fit_scaler=True)

        # TabNet için doğrulama seti (validation set) ayıralım
        val_split_idx = int(len(X_np) * 0.8)
        X_tr, X_val = X_np[:val_split_idx], X_np[val_split_idx:]
        y_tr, y_val = y_np[:val_split_idx], y_np[val_split_idx:]

        if len(X_tr) == 0 or len(X_val) == 0:
            raise ValueError("Eğitim veya doğrulama için veri yetersiz.")

        self.model.fit(
            X_train=X_tr, y_train=y_tr,
            eval_set=[(X_val, y_val)],
            patience=self.model_specific_params.get('patience', 15),
            max_epochs=self.model_specific_params.get('max_epochs', 100),
            batch_size=self.model_specific_params.get('batch_size', 1024)
        )
        self.is_trained = True

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained: raise ModelNotTrainedError("Model eğitilmemiş.")
        X_np, _ = self._prepare_data(X, fit_scaler=False)
        proba = self.model.predict_proba(X_np)[:, 1]
        threshold = self.model_specific_params.get('threshold', 0.5)
        return (proba >= threshold).astype(int)