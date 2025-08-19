from __future__ import annotations
from .base_ai_model import BaseAIModel
class LightGBMModel(BaseAIModel):
    def _initialize_model(self, params=None):
        import lightgbm as lgb
        self.model = lgb.LGBMClassifier(
            n_estimators=300,
            max_depth=-1,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
        )
