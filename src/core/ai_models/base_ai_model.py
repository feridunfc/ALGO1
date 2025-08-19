# strategies/ai_models/base_ai_model.py
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable
import joblib
import pandas as pd
import numpy as np

# BU ŞEKİLDE DEĞİŞTİRİN (Kendi dosya yollarınıza göre):
from config.config import AppConfig as MainConfig # AppConfig'i MainConfig olarak isimlendirelim ki kodun geri kalanı çalışsın
import logging # Veya kendi logger'ınızı import edin
# logger = get_app_logger(__name__) yerine şunu kullanın:
logger = logging.getLogger(__name__)

try:
    from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import classification_report, accuracy_score, f1_score

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import optuna

    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

logger = get_app_logger(__name__)


# --- Özel Hata Sınıfları ---
class AIModelError(Exception): pass


class DataPreparationError(AIModelError): pass


class ModelNotTrainedError(AIModelError): pass


class FeatureMismatchError(AIModelError): pass


# --- Ana Temel Sınıf ---
class BaseAIModel(ABC):
    def __init__(self, model_name: str, config: MainConfig):
        self.model_name = model_name.lower()
        self.config = config
        self.params = self._load_params()

        # [KESİN DÜZELTME] optimization_params'ı doğrudan config nesnesinden alıyoruz.
        self.optimization_params = self.config.ai_models.optimization

        self.scaler_type = self.params.get('scaler_type', 'minmax')
        self.scaler = self._initialize_scaler()

        self.model: Any = None
        self.features: List[str] = self.params.get('feature_columns', [])
        self.is_trained: bool = False
        self.is_optimized: bool = False
        self.best_params: Optional[Dict[str, Any]] = None

        if not self.features:
            raise ValueError(f"'{self.model_name}' için config'de 'feature_columns' belirtilmemiş.")

        logger.info(
            f"'{self.model_name}' stratejisi başlatıldı. Scaler: {self.scaler_type}. Features: {len(self.features)} adet.")

    def _load_params(self) -> Dict[str, Any]:
        base_model_name = "_".join(self.model_name.split("_")[1:]) if "_" in self.model_name else self.model_name
        model_params = getattr(self.config.ai_models, base_model_name, None)
        if model_params is None or not isinstance(model_params, dict):
            logger.warning(f"Config'de '{base_model_name}' için özel ayar bulunamadı.")
            return {}
        return model_params

    def _initialize_scaler(self) -> Optional[Any]:
        if not SKLEARN_AVAILABLE: return None
        scaler_map = {'standard': StandardScaler, 'minmax': MinMaxScaler, 'robust': RobustScaler}
        scaler_class = scaler_map.get(self.scaler_type)
        return scaler_class() if scaler_class else None

    def _prepare_data(self, X: pd.DataFrame, y: Optional[pd.Series] = None, fit_scaler: bool = False) -> Tuple[
        np.ndarray, Optional[np.ndarray]]:
        if not self.features: raise FeatureMismatchError("Özellik listesi (features) ayarlanmamış.")
        missing_features = set(self.features) - set(X.columns)
        if missing_features: raise FeatureMismatchError(f"Gelen veride eksik özellikler var: {missing_features}")

        X_feat = X[self.features].copy()
        if X_feat.isnull().values.any():
            X_feat.ffill(inplace=True);
            X_feat.bfill(inplace=True)
            if X_feat.isnull().values.any(): raise DataPreparationError("NaN doldurma sonrası hala eksik veri var.")

        X_np = X_feat.values.astype(np.float32)
        y_np = y.values.astype(int) if y is not None else None

        if self.scaler:
            if fit_scaler:
                X_np = self.scaler.fit_transform(X_np)
            else:
                if not hasattr(self.scaler, 'scale_'): raise AIModelError(
                    "Scaler eğitilmemiş, ancak transform isteniyor.")
                X_np = self.scaler.transform(X_np)
        return X_np, y_np

    @abstractmethod
    def _initialize_model(self, params: Optional[Dict[str, Any]] = None):
        pass

    @abstractmethod
    def train(self, X_train: pd.DataFrame, y_train: pd.Series, **kwargs):
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        pass

    @abstractmethod
    def _get_optuna_objective(self, X: np.ndarray, y: np.ndarray, cv_strategy: Any) -> Callable:
        pass

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, Any]:
        if not self.is_trained: raise ModelNotTrainedError("Değerlendirme yapılamıyor: Model eğitilmemiş.")
        if not SKLEARN_AVAILABLE:
            logger.warning("Sklearn mevcut değil. Detaylı metrikler hesaplanamıyor.")
            return {}

        y_pred = self.predict(X_test)
        common_index = y_test.index.intersection(X_test.index)
        y_test_aligned = y_test.loc[common_index]

        if len(y_pred) != len(X_test):
            y_test_aligned = y_test_aligned.iloc[-len(y_pred):]
        if len(y_pred) != len(y_test_aligned):
            raise AIModelError(f"Tahmin ve gerçek etiket uzunlukları uyuşmuyor: {len(y_pred)} vs {len(y_test_aligned)}")

        accuracy = accuracy_score(y_test_aligned, y_pred)
        f1 = f1_score(y_test_aligned, y_pred, average='weighted', zero_division=0)

        results = {'accuracy': accuracy, 'f1_weighted': f1}
        logger.info(f"Model Değerlendirme Sonuçları: Accuracy={accuracy:.2%}, F1-Score={f1:.3f}")
        return results

    def optimize_parameters(self, X_train: pd.DataFrame, y_train: pd.Series) -> Dict[str, Any]:
        if not OPTUNA_AVAILABLE: raise ImportError("Optimizasyon için 'optuna' kütüphanesi gerekli.")

        # [KESİN DÜZELTME] .get() yerine doğrudan dataclass özelliğine erişim
        if not self.optimization_params.enabled:
            logger.info("Optimizasyon config'de kapalı. Atlanıyor.")
            return {}

        logger.info(f"'{self.model_name}' için Optuna hiperparametre optimizasyonu başlatılıyor...")

        X_np, y_np = self._prepare_data(X_train, y_train, fit_scaler=True)
        cv_strategy = TimeSeriesSplit(n_splits=self.optimization_params.cv_folds)

        study = optuna.create_study(direction="maximize")
        objective_func = self._get_optuna_objective(X_np, y_np, cv_strategy)

        timeout = self.optimization_params.timeout_seconds
        study.optimize(
            objective_func,
            n_trials=self.optimization_params.n_trials,
            timeout=timeout if timeout > 0 else None
        )

        self.is_optimized = True
        self.best_params = study.best_trial.params
        best_score = study.best_trial.value

        logger.info("Optimizasyon tamamlandı.")
        logger.info(f"  En iyi F1-Skoru: {best_score:.4f}")
        logger.info(f"  En iyi parametreler: {self.best_params}")

        self.params.update(self.best_params)
        return self.best_params

    def save(self):
        if not self.is_trained: raise ModelNotTrainedError("Model eğitilmemiş, kaydedilemiyor.")

        save_dir = Path(self.config.ai_models.model_save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        # Keras/TF modelleri kendi save/load metodunu kullanmalı
        if hasattr(self.model, 'save'):
            model_path = save_dir / f"{self.model_name}.keras"
            self.model.save(model_path)

        filepath = save_dir / f"{self.model_name}.joblib"
        data_to_save = {
            'scaler': self.scaler,
            'features': self.features,
            'params': self.params,
        }
        try:
            joblib.dump(data_to_save, filepath)
            logger.info(f"Model durumu '{filepath}' adresine başarıyla kaydedildi.")
        except Exception as e:
            logger.error(f"Model durumu kaydedilirken hata: {e}", exc_info=True)

    def load(self):
        save_dir = Path(self.config.ai_models.model_save_dir)
        filepath = save_dir / f"{self.model_name}.joblib"
        if not filepath.exists():
            logger.warning(f"Yüklenecek model durumu dosyası bulunamadı: {filepath}")
            return

        try:
            loaded_data = joblib.load(filepath)
            self.scaler = loaded_data['scaler']
            self.features = loaded_data['features']
            self.params = loaded_data['params']

            if hasattr(self, 'model') and hasattr(self.model, 'load_weights'):
                model_path = save_dir / f"{self.model_name}.keras"
                if model_path.exists():
                    from tensorflow.keras.models import load_model
                    self.model = load_model(model_path)
                else:
                    logger.warning(f"Model dosyası bulunamadı: {model_path}. Sadece durum yüklendi.")

            self.is_trained = True
            logger.info(f"Model durumu '{filepath}' adresinden başarıyla yüklendi.")
        except Exception as e:
            logger.error(f"Model yüklenirken hata: {e}", exc_info=True)