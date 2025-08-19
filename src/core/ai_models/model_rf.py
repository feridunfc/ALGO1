import numpy as np
import pandas as pd
from .base_ai_model import BaseAIModel, ModelNotTrainedError, MainConfig

try:
    from sklearn.ensemble import RandomForestClassifier

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class RandomForestModel(BaseAIModel):
    def __init__(self, config: MainConfig, model_params: dict):
        # BaseAIModel'e model adı ve ana config'i gönder
        super().__init__(model_name='random_forest', config=config)
        # Bu modele özel parametreleri sakla
        self.model_specific_params = model_params

    def _initialize_model(self, params=None):
        if not SKLEARN_AVAILABLE: raise ImportError("RandomForest için scikit-learn gerekli.")

        # Parametreleri birleştir: öncelik optimizasyondan gelen veya modele özel olanlarda
        current_params = self.params.copy()  # config'den gelen temel
        current_params.update(self.model_specific_params)  # stratejiden gelen özel
        if params: current_params.update(params)

        self.model = RandomForestClassifier(
            n_estimators=current_params.get('n_estimators', 100),
            max_depth=current_params.get('max_depth', None),
            random_state=42, n_jobs=-1
        )

    def train(self, X_train: pd.DataFrame, y_train: pd.Series, **kwargs):
        self._initialize_model(self.best_params or {})
        X_np, y_np = self._prepare_data(X_train, y_train, fit_scaler=True)
        self.model.fit(X_np, y_np)
        self.is_trained = True

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained: raise ModelNotTrainedError("Model eğitilmemiş.")
        X_np, _ = self._prepare_data(X, fit_scaler=False)
        proba = self.model.predict_proba(X_np)[:, 1]
        threshold = self.model_specific_params.get('threshold', 0.5)
        return (proba >= threshold).astype(int)

    def _get_optuna_objective(self, X, y, cv_strategy):
        # Gerekirse bu metodu doldurarak Optuna'nın davranışını özelleştirebilirsiniz.
        # Şimdilik BaseAIModel'deki varsayılanı kullanması için boş bırakabiliriz.
        pass