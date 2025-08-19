# engines/anomaly_detector.py
import numpy as np, pandas as pd
from typing import Optional, Any, TYPE_CHECKING
from utils.app_logger import get_app_logger

try:
    from pyod.models.ecod import ECOD
    from pyod.models.iforest import IForest
    PYOD_AVAILABLE = True
except ImportError:
    PYOD_AVAILABLE = False
    ECOD = IForest = None

try:
    from sklearn.preprocessing import RobustScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    RobustScaler = None

if TYPE_CHECKING:
    from config.main_config import MainConfig

class AnomalyDetector:
    def __init__(self, config: 'MainConfig'):
        self.config = config
        self.ad_config = config.anomaly
        self.logger = get_app_logger("AnomalyDetector")
        self.model_type = getattr(self.ad_config, "model_type", "ecod")
        self.contamination = getattr(self.ad_config, "contamination", 0.1)
        self.min_data_points = getattr(self.ad_config, "min_data_points", 50)
        self.feature_columns = getattr(self.ad_config, "feature_columns", ["close","volume"])
        self.normalization_method = getattr(self.ad_config, "normalization_method", "robust")
        self.model = self._init_model()

    def _init_model(self) -> Optional[Any]:
        if not PYOD_AVAILABLE:
            self.logger.warning("PyOD yok → anomali atlanacak.")
            return None
        try:
            if self.model_type == "ecod" and ECOD:
                return ECOD(contamination=self.contamination, n_jobs=1)
            if self.model_type == "isolation_forest" and IForest:
                return IForest(contamination=self.contamination, n_jobs=-1, random_state=42)
            self.logger.error(f"Bilinmeyen anomali modeli: {self.model_type}")
        except Exception as e:
            self.logger.error(f"Model init hatası: {e}", exc_info=True)
        return None

    def add_scores(self, data: pd.DataFrame) -> pd.DataFrame:
        """DataFrame'e anomaly_score ekler; orijinal index/sütun düzeni korunur."""
        if self.model is None:
            data = data.copy()
            data["anomaly_score"] = 0.5
            return data

        if "symbol" not in data.columns:
            self.logger.error("'symbol' sütunu yok → anomaly_score=0.5")
            data = data.copy()
            data["anomaly_score"] = 0.5
            return data

        # Her sembol için skor üret
        pieces = []
        for sym, grp in data.groupby("symbol", group_keys=False):
            pieces.append(self._score_one_symbol(grp))
        scored = pd.concat(pieces).sort_index()

        # Orijinal DF’ye tek sütun merge (index üzerinden) – bütünlük korunur
        out = data.copy()
        if "anomaly_score" in out.columns:
            out = out.drop(columns=["anomaly_score"])
        out = out.merge(scored[["anomaly_score"]], left_index=True, right_index=True, how="left")
        out["anomaly_score"] = out["anomaly_score"].fillna(0.5)
        return out

    def _score_one_symbol(self, df: pd.DataFrame) -> pd.DataFrame:
        res = pd.DataFrame(index=df.index, data={"anomaly_score": 0.5})
        if df.shape[0] < self.min_data_points:
            return res

        feats = [c for c in self.feature_columns if c in df.columns]
        X = df[feats].dropna()
        if X.empty:
            return res

        Xv = X.values
        if SKLEARN_AVAILABLE and self.normalization_method == "robust":
            try:
                scaler = RobustScaler()
                Xv = scaler.fit_transform(Xv)
            except Exception:
                self.logger.warning("RobustScaler atlandı (NaN/Inf olabilir).")

        try:
            self.model.fit(Xv)
            scores = self.model.decision_scores_.astype(float)
            # [0,1] normalize
            lo, hi = float(np.min(scores)), float(np.max(scores))
            z = 0.5 if hi <= lo else (scores - lo) / (hi - lo)
            res.loc[X.index, "anomaly_score"] = np.clip(z, 0, 1)
        except Exception as e:
            self.logger.error(f"{df['symbol'].iloc[0]} skorlama hatası: {e}", exc_info=False)
        return res
