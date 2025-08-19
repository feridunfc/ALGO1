from __future__ import annotations
from .base_ai_model import BaseAIModel
from sklearn.ensemble import RandomForestClassifier
class RandomForestModel(BaseAIModel):
    def _initialize_model(self, params=None):
        if params is None:
            params = {}
        self.model = RandomForestClassifier(
            n_estimators=int(params.get("n_estimators", 200)),
            max_depth=params.get("max_depth", None),
            random_state=42,
            n_jobs=-1,
        )
