from __future__ import annotations
from .base_ai_model import BaseAIModel
class XGBoostModel(BaseAIModel):
    def _initialize_model(self, params=None):
        import xgboost as xgb
        self.model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            n_jobs=-1,
        )
