
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

class AnomalyType(Enum):
    PRICE_SPIKE = auto()
    VOLUME_SURGE = auto()
    SENTIMENT_SHIFT = auto()
    SOCIAL_TREND = auto()

@dataclass
class AnomalyAlert:
    timestamp: datetime
    metric: str
    value: float
    baseline: float
    anomaly_type: AnomalyType
    severity: float  # 0..1
    confidence: float
    description: str
    metadata: Optional[Dict] = None

class AnomalyDetector:
    def __init__(self, config: Dict):
        self.config = {
            "price": {"model": "isolation_forest", "params": {"contamination": 0.05}, "window": "24h"},
            "volume": {"model": "zscore", "params": {"threshold": 3.0}, "window": "1h"},
            "sentiment": {"model": "rolling_quantile", "params": {"quantile": 0.99}, "window": "6h"},
            **(config or {}),
        }
        self.models: Dict[str, object] = {}
        self.history = pd.DataFrame(columns=["timestamp", "metric", "value"])
        self._initialize_models()

    def _initialize_models(self):
        for metric, cfg in self.config.items():
            if cfg.get("model") == "isolation_forest":
                self.models[metric] = IsolationForest(n_estimators=100, **cfg.get("params", {}))
            elif cfg.get("model") == "dbscan":
                self.models[metric] = DBSCAN(eps=0.5, min_samples=10, **cfg.get("params", {}))

    def detect(self, data: pd.DataFrame) -> List[AnomalyAlert]:
        alerts: List[AnomalyAlert] = []
        if data is None or data.empty:
            return alerts

        # Ensure proper types
        df = data.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.sort_values("timestamp")
        self._update_history(df)

        for metric, group in df.groupby("metric"):
            if metric not in self.config:
                continue
            cfg = self.config[metric]
            vals = group["value"].astype(float).values.reshape(-1, 1)

            if cfg["model"] == "isolation_forest":
                if len(vals) >= 10:
                    model = self.models.get(metric) or IsolationForest(**cfg.get("params", {}))
                    preds = model.fit_predict(vals)
                    scores = model.decision_function(vals)
                    for i, (p, s) in enumerate(zip(preds, scores)):
                        if p == -1:
                            alerts.append(
                                self._create_alert(
                                    metric=metric,
                                    value=float(vals[i][0]),
                                    score=float(-s),  # invert: more negative => more severe
                                    timestamp=pd.to_datetime(group.iloc[i]["timestamp"]).to_pydatetime(),
                                )
                            )

            elif cfg["model"] == "zscore":
                window = self._get_history_window(metric)
                if window.size >= 10:
                    mean = float(np.mean(window))
                    std = float(np.std(window))
                    if std > 0:
                        z = (vals - mean) / std
                        thr = float(cfg["params"].get("threshold", 3.0))
                        for i, zv in enumerate(z):
                            if abs(zv[0]) > thr:
                                alerts.append(
                                    self._create_alert(
                                        metric=metric,
                                        value=float(vals[i][0]),
                                        score=float(abs(zv[0])),
                                        timestamp=pd.to_datetime(group.iloc[i]["timestamp"]).to_pydatetime(),
                                        baseline=mean,
                                    )
                                )
        return alerts

    def _create_alert(self, metric: str, value: float, score: float, timestamp: datetime, baseline: Optional[float] = None) -> AnomalyAlert:
        a_type = {
            "price": AnomalyType.PRICE_SPIKE,
            "volume": AnomalyType.VOLUME_SURGE,
            "sentiment": AnomalyType.SENTIMENT_SHIFT,
        }.get(metric, AnomalyType.SOCIAL_TREND)
        severity = min(1.0, score / 5.0)
        return AnomalyAlert(
            timestamp=timestamp,
            metric=metric,
            value=value,
            baseline=baseline or 0.0,
            anomaly_type=a_type,
            severity=severity,
            confidence=min(0.99, severity * 1.2),
            description=f"{metric} anomaly detected (score={score:.2f})",
        )

    def _update_history(self, new_data: pd.DataFrame):
        self.history = pd.concat([self.history, new_data[["timestamp", "metric", "value"]]]).drop_duplicates()
        # Trim by window per-metric
        keep_mask = pd.Series([True] * len(self.history), index=self.history.index)
        now = pd.Timestamp.utcnow()
        for metric, cfg in self.config.items():
            td = pd.to_timedelta(cfg.get("window", "24h"))
            cutoff = now - td
            if "timestamp" in self.history.columns:
                if metric in self.history["metric"].values:
                    keep_mask &= ~((self.history["metric"] == metric) & (self.history["timestamp"] < cutoff))
        self.history = self.history[keep_mask]

    def _get_history_window(self, metric: str) -> np.ndarray:
        if self.history.empty:
            return np.array([])
        td = pd.to_timedelta(self.config.get(metric, {}).get("window", "24h"))
        cutoff = pd.Timestamp.utcnow() - td
        sel = self.history[(self.history["metric"] == metric) & (self.history["timestamp"] >= cutoff)]
        return sel["value"].astype(float).to_numpy()
