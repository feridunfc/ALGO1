# src/ai/base_strategy.py
"""
Base class for AI-driven trading strategies.
- Güvenli Config / Logger import (fallback'lı)
- İsteğe bağlı sklearn/optuna/imblearn kullanım bayrakları
- Tutarlı veri hazırlama (_prepare_data), SMOTE, CV seçimi
- Model kaydet/yükle, sinyal üretimi ve değerlendirme yardımcıları
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type, Union, Callable
import sys
import json
import joblib
import numpy as np
import pandas as pd

# --- StrategyParameters shim ---------------------------------------------------
# Tercihen base.py'deki StrategyParameters'ı kullan; yoksa minimal bir tanım oluştur.
try:
    from .base import StrategyParameters  # tek kaynak
except Exception:
    try:
        from pydantic import BaseModel
    except Exception:
        class BaseModel:  # type: ignore
            pass

    class StrategyParameters(BaseModel):  # type: ignore
        """AI stratejileri için parametre şeması (shim)."""
        pass
# ------------------------------------------------------------------------------

# --- Config & Logger (güvenli import + fallback) ---
Config: Any = None
bs_logger: Any = None

try:
    # Proje kökü sys.path'te değilse ekle
    from pathlib import Path as _Path
    _here = _Path(__file__).resolve()
    _root = _here.parents[2] if (_here.name == "base_strategy.py") else _here.parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

    try:
        from src.core.config import Config as _ImportedConfig
    except Exception:
        from config.config import Config as _ImportedConfig  # bazı repo düzenlerinde "src." prefiksi olmayabilir

    try:
        from src.utils.app_logger import get_app_logger as _get_logger
    except Exception:
        from utils.app_logger import get_app_logger as _get_logger

    Config = _ImportedConfig
    bs_logger = _get_logger("AIBaseStrategy")
except Exception as _e:
    import logging
    bs_logger = logging.getLogger("AIBaseStrategyFallback")
    if not bs_logger.handlers:
        _h = logging.StreamHandler()
        _h.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
        bs_logger.addHandler(_h)
    bs_logger.setLevel(logging.INFO)

    class _FallbackConfig:
        MODEL_PARAMS: Dict[str, Dict[str, Any]] = {}
        USE_SMOTE_SAMPLING: bool = False
        MODEL_SAVE_DIR: Path = Path("./saved_models")
        OPTIMIZABLE_MODELS: List[str] = []
        AI_SIGNAL_PARAMS: Dict[str, Any] = {}
        PROJECT_ROOT_PATH: Path = Path(".")
        SKLEARN_AVAILABLE = False
        OPTUNA_AVAILABLE = False
        IMBLEARN_AVAILABLE = False
        OPTIMIZATION_PARAMS: Dict[str, Any] = {
            "enable_optimization": False,
            "n_trials": 20,
            "optuna_timeout_seconds": None,
            "cv_folds": 3,
            "scoring_metric": "f1_weighted",
            "optuna_study_name_prefix": "opt_study",
            "enable_optuna_storage": False,
            "optuna_storage_db": "",
            "use_median_pruner": True,
            "pruner_n_startup_trials": 5,
            "pruner_n_warmup_steps": 0,
            "use_tpe_sampler": True,
            "sampler_n_startup_trials": 10,
        }

    Config = _FallbackConfig  # type: ignore[arg-type]
    bs_logger.critical("Config/Logger import edilemedi; fallback kullanılıyor.")

# --- opsiyonel bağımlılıklar ---
SKLEARN_OK = bool(getattr(Config, "SKLEARN_AVAILABLE", False))
OPTUNA_OK = bool(getattr(Config, "OPTUNA_AVAILABLE", False))
IMBLEARN_OK = bool(getattr(Config, "IMBLEARN_AVAILABLE", False))

# sklearn
StandardScaler = MinMaxScaler = RobustScaler = LabelEncoder = object
TimeSeriesSplit = StratifiedKFold = KFold = GroupKFold = object
accuracy_score = f1_score = classification_report = confusion_matrix = roc_auc_score = make_scorer = object
Pipeline = clone = object

if SKLEARN_OK:
    try:
        from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler, LabelEncoder  # type: ignore
        from sklearn.model_selection import (
            TimeSeriesSplit,
            cross_val_score,
            StratifiedKFold,
            KFold,
            GroupKFold,
        )  # type: ignore
        from sklearn.metrics import (
            accuracy_score,
            f1_score,
            classification_report,
            confusion_matrix,
            roc_auc_score,
            make_scorer,
        )  # type: ignore
        from sklearn.pipeline import Pipeline  # type: ignore
        from sklearn.base import clone  # type: ignore
    except Exception:
        SKLEARN_OK = False
        bs_logger.warning("sklearn import başarısız; SKLEARN_AVAILABLE=False olarak devam.")

# optuna
optuna = None
if OPTUNA_OK:
    try:
        import optuna  # type: ignore
    except Exception:
        OPTUNA_OK = False
        bs_logger.warning("optuna import başarısız; OPTUNA_AVAILABLE=False olarak devam.")

# imblearn
SMOTE = None
if IMBLEARN_OK:
    try:
        from imblearn.over_sampling import SMOTE  # type: ignore
    except Exception:
        IMBLEARN_OK = False
        bs_logger.warning("imblearn/SMOTE import başarısız; IMBLEARN_AVAILABLE=False olarak devam.")

# --- yardımcılar ---
SCALER_MAP: Dict[Optional[str], Optional[Type]] = {
    "standard": StandardScaler if SKLEARN_OK else None,
    "minmax": MinMaxScaler if SKLEARN_OK else None,
    "robust": RobustScaler if SKLEARN_OK else None,
    None: None,
}

# --- özel istisnalar ---
class StrategyError(Exception): ...
class DataPreparationError(StrategyError): ...
class ModelNotTrainedError(StrategyError): ...
class FeatureMismatchError(StrategyError): ...
class OptimizationError(StrategyError): ...


class BaseStrategy(ABC):
    """
    AI tabanlı stratejiler için temel sınıf.
    Alt sınıflar: _initialize_model, train, predict, predict_proba, _get_optuna_objective implement etmeli.
    """

    def __init__(self, model_type: str, params: Optional[Dict[str, Any]] = None, config_obj: Optional[Any] = None):
        self.model_type = model_type.lower()
        self._logger = bs_logger

        # Config seçimi
        if config_obj is not None:
            self.config = config_obj
        else:
            try:
                self.config = Config() if callable(Config) else Config  # type: ignore
            except Exception:
                self.config = Config  # type: ignore

        # bağımlılık durumları
        self.sklearn_ok = SKLEARN_OK
        self.optuna_ok = OPTUNA_OK
        self.imblearn_ok = IMBLEARN_OK

        # paramlar (Config.MODEL_PARAMS ile birleşik)
        self.params: Dict[str, Any] = {}
        try:
            defaults = getattr(self.config, "MODEL_PARAMS", {}).get(self.model_type, {})
            self.params.update(defaults)
        except Exception:
            pass
        if params:
            p = params.copy()
            p.pop("config_obj", None)
            self.params.update(p)

        # scaler
        self.scaler_type: Optional[str] = self.params.get("scaler_type")
        self._scaler_cls: Optional[Type] = SCALER_MAP.get(self.scaler_type)
        self.scaler = self._scaler_cls() if (self._scaler_cls and self.sklearn_ok) else None

        # model durumu
        self.model: Any = None
        self.features: List[str] = []
        self.classes_: Optional[np.ndarray] = None
        self.is_trained: bool = False
        self.is_optimized: bool = False
        self.best_params_optuna: Optional[Dict[str, Any]] = None
        self.best_score: Optional[float] = None
        self.optuna_study: Optional[Any] = None

        self._logger.info(f"[{self.model_type.upper()}] init: scaler={self.scaler_type or 'disabled'}")

    # ---------- public API ----------
    def set_features(self, features: List[str]):
        if not isinstance(features, list) or not all(isinstance(f, str) for f in features):
            raise TypeError("features list[str] olmalı")
        self.features = features

    def get_params(self) -> Dict[str, Any]:
        model_params = {}
        if self.model is not None and hasattr(self.model, "get_params") and callable(self.model.get_params):
            try:
                model_params = self.model.get_params()
            except Exception:
                pass
        return {**self.params, **model_params}

    def save_model(self, filepath_prefix: Optional[str] = None) -> Optional[str]:
        if not self.is_trained or self.model is None:
            raise ModelNotTrainedError(f"{self.model_type} eğitilmemiş; kaydedilemez.")
        save_dir: Path = getattr(self.config, "MODEL_SAVE_DIR", Path("./saved_models"))  # type: ignore
        save_dir.mkdir(parents=True, exist_ok=True)

        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        base = filepath_prefix or f"{ts}_{self.model_type}"
        path = (save_dir / str(base)).with_suffix(".joblib")

        payload = {
            "model": self.model,
            "scaler": self.scaler,
            "scaler_type": self.scaler_type,
            "features": self.features,
            "classes_": self.classes_,
            "params": self.params,
            "model_type": self.model_type,
            "is_trained": self.is_trained,
            "is_optimized": self.is_optimized,
            "best_params_optuna": self.best_params_optuna,
            "best_score": self.best_score,
        }
        try:
            joblib.dump(payload, path)
            self._logger.info(f"Model kaydedildi: {path}")
            return str(path)
        except Exception as e:
            self._logger.error(f"Model kaydedilemedi: {e}", exc_info=True)
            return None

    def load_from_saved(self, filepath: Union[str, Path]) -> bool:
        p = Path(filepath)
        if not p.exists():
            self._logger.error(f"Model dosyası yok: {p}")
            return False
        try:
            data = joblib.load(p)
            if data.get("model_type") != self.model_type:
                self._logger.error("Model türü uyuşmuyor.")
                return False
            self.model = data.get("model")
            self.scaler = data.get("scaler")
            self.scaler_type = data.get("scaler_type")
            self.features = data.get("features", [])
            self.classes_ = data.get("classes_")
            self.params.update(data.get("params", {}))
            self.is_trained = data.get("is_trained", False)
            self.is_optimized = data.get("is_optimized", False)
            self.best_params_optuna = data.get("best_params_optuna")
            self.best_score = data.get("best_score")
            if not self.is_trained or self.model is None:
                raise ModelNotTrainedError("Yüklenen model geçersiz.")
            self._logger.info(f"Model yüklendi: {p}")
            return True
        except Exception as e:
            self._logger.error(f"Model yüklenemedi: {e}", exc_info=True)
            self.is_trained = False
            return False

    def get_signal(self, row: Union[pd.Series, Dict[str, Any]], thresholds: Optional[Dict[str, float]] = None) -> int:
        if not self.is_trained or self.model is None or not self.features:
            return 0

        thr = thresholds or getattr(self.config, "AI_SIGNAL_PARAMS", {})  # type: ignore
        buy_thr = float(thr.get("buy_confidence_threshold", 0.55))
        sell_thr = float(thr.get("sell_confidence_threshold", 0.55))
        gap_thr = float(thr.get("confidence_gap_threshold", 0.10))

        try:
            if isinstance(row, dict):
                X = pd.DataFrame([row])[self.features]
            else:
                X = pd.DataFrame([row[self.features]])
            if X.isnull().any().any():
                return 0
            proba = self.predict_proba(X)
            if proba is None or proba.size == 0 or self.classes_ is None:
                return 0
            proba = np.asarray(proba)
            labels = list(self.classes_)
            d = {labels[i]: float(proba[0, i]) for i in range(len(labels))}
            pb, ps, ph = d.get(1, 0.0), d.get(-1, 0.0), d.get(0, 0.0)

            if pb > buy_thr and pb - max(ps, ph) >= gap_thr:
                return 1
            if ps > sell_thr and ps - max(pb, ph) >= gap_thr:
                return -1
            return 0
        except Exception:
            return 0

    def evaluate_model(self, X_test: Union[pd.DataFrame, np.ndarray], y_test: pd.Series) -> Dict[str, Any]:
        if not self.is_trained or self.model is None or not self.features:
            return {"error": "Model hazır değil."}
        try:
            Xp, yp = self._prepare_data(X_test, y_test, fit_scaler=False)
        except StrategyError as e:
            return {"error": f"Veri hazırlama hatası: {e}"}

        try:
            y_pred = self.predict(Xp)
            if y_pred is None or len(y_pred) != len(yp):
                return {"error": "Tahmin hatası"}
            out: Dict[str, Any] = {}

            if SKLEARN_OK:
                try:
                    out["accuracy"] = accuracy_score(yp, y_pred)  # type: ignore
                except Exception:
                    out["accuracy"] = np.nan
                try:
                    labels = sorted(set(yp) | set(y_pred))
                    out["f1_weighted"] = f1_score(yp, y_pred, labels=labels, average="weighted", zero_division=0)  # type: ignore
                    out["classification_report_str"] = classification_report(  # type: ignore
                        yp, y_pred, labels=labels, zero_division=0
                    )
                    out["confusion_matrix"] = confusion_matrix(yp, y_pred, labels=labels).tolist()  # type: ignore
                except Exception:
                    pass

                # ROC AUC (mümkünse)
                try:
                    if hasattr(self, "predict_proba"):
                        proba = self.predict_proba(Xp)
                        if proba is not None and proba.shape[1] >= 2:
                            classes = self.classes_ if self.classes_ is not None else np.unique(yp)
                            if len(classes) == 2:
                                pos = 1 if 1 in classes else classes[1]
                                idx = list(classes).index(pos)
                                y_bin = (yp == pos).astype(int)
                                if len(np.unique(y_bin)) > 1:
                                    out["roc_auc"] = roc_auc_score(y_bin, proba[:, idx])  # type: ignore
                except Exception:
                    pass
            return out
        except Exception as e:
            return {"error": f"Değerlendirme hatası: {e}"}

    # ---------- veri hazırlama / CV / SMOTE ----------
    def _prepare_data(
        self, X: Union[pd.DataFrame, np.ndarray], y: Optional[pd.Series] = None, fit_scaler: bool = False
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        if not self.features:
            raise FeatureMismatchError("Özellik listesi boş.")

        if isinstance(X, pd.DataFrame):
            missing = set(self.features) - set(X.columns)
            if missing:
                raise FeatureMismatchError(f"Eksik özellikler: {missing}")
            Xdf = X[self.features].copy()
        elif isinstance(X, np.ndarray):
            if X.ndim == 1 and len(self.features) == 1:
                X = X.reshape(-1, 1)
            if X.shape[1] != len(self.features):
                raise FeatureMismatchError(
                    f"X kolonu {X.shape[1]}, beklenen {len(self.features)}"
                )
            Xdf = pd.DataFrame(X, columns=self.features)
        else:
            raise TypeError("X DataFrame veya ndarray olmalı.")

        # NaN/Inf temizliği
        Xdf = Xdf.ffill().bfill()
        if Xdf.isnull().any().any() or not np.isfinite(Xdf.to_numpy()).all():
            raise DataPreparationError("X içinde NaN/Inf kaldı.")

        y_np: Optional[np.ndarray] = None
        if y is not None:
            if not isinstance(y, pd.Series):
                raise TypeError("y Series olmalı.")
            if len(y) != len(Xdf):
                y = y.reindex(Xdf.index)
            if y.isnull().any():
                valid = ~y.isnull()
                Xdf = Xdf[valid]
                y = y[valid]
            if Xdf.empty:
                raise DataPreparationError("Veri boş kaldı.")
            y_np = y.astype(int).to_numpy()

        X_np = Xdf.to_numpy(dtype=np.float32)

        if self.scaler is not None and SKLEARN_OK and X_np.shape[0] > 0:
            try:
                if fit_scaler:
                    X_np = self.scaler.fit_transform(X_np)  # type: ignore
                else:
                    if hasattr(self.scaler, "n_features_in_"):  # type: ignore
                        X_np = self.scaler.transform(X_np)  # type: ignore
            except Exception as e:
                raise DataPreparationError(f"Ölçekleme hatası: {e}")

        if not np.isfinite(X_np).all():
            raise DataPreparationError("Ölçekleme sonrası NaN/Inf tespit edildi.")
        if y_np is not None and len(X_np) != len(y_np):
            raise DataPreparationError("X ve y uzunlukları uyuşmuyor.")
        return X_np, y_np

    def _apply_smote_if_enabled(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        if not getattr(self.config, "USE_SMOTE_SAMPLING", False) or not IMBLEARN_OK or SMOTE is None:
            return X, y
        try:
            vc = pd.Series(y).value_counts()
            if len(vc) < 2:
                return X, y
            k = min(5, max(1, int(vc.min()) - 1))
            if k < 1:
                return X, y
            sm = SMOTE(random_state=42, k_neighbors=k)  # type: ignore
            return sm.fit_resample(X, y)
        except Exception:
            return X, y

    def get_cv_strategy(
        self, X: np.ndarray, y: np.ndarray, cv_type: Optional[str] = None, n_splits: int = 5, test_size_ts: Optional[int | float] = None
    ) -> Any:
        if not SKLEARN_OK:
            return max(2, n_splits)
        t = cv_type or self.params.get("cv_type", "timeseries")
        if t == "timeseries":
            try:
                return TimeSeriesSplit(n_splits=max(2, n_splits), test_size=test_size_ts or None, gap=0)  # type: ignore
            except Exception:
                return KFold(n_splits=max(2, n_splits), shuffle=True, random_state=42)  # type: ignore
        if t == "stratified":
            try:
                return StratifiedKFold(n_splits=max(2, n_splits), shuffle=True, random_state=42)  # type: ignore
            except Exception:
                return KFold(n_splits=max(2, n_splits), shuffle=True, random_state=42)  # type: ignore
        return KFold(n_splits=max(2, n_splits), shuffle=True, random_state=42)  # type: ignore

    # ---------- alt sınıfların implement etmesi gerekenler ----------
    @abstractmethod
    def _initialize_model(self, params: Optional[Dict[str, Any]] = None) -> None: ...
    @abstractmethod
    def train(self, X_train: pd.DataFrame, y_train: pd.Series, **kwargs) -> bool: ...
    @abstractmethod
    def predict(self, X: Union[pd.DataFrame, np.ndarray]) -> Optional[np.ndarray]: ...
    @abstractmethod
    def predict_proba(self, X: Union[pd.DataFrame, np.ndarray]) -> Optional[np.ndarray]: ...
    @abstractmethod
    def _get_optuna_objective(self, X_np: np.ndarray, y_np: np.ndarray, cv_strategy: Any) -> Callable[[Any], float]: ...


__all__ = [
    "BaseStrategy",
    "StrategyError",
    "DataPreparationError",
    "ModelNotTrainedError",
    "FeatureMismatchError",
    "OptimizationError",
]
