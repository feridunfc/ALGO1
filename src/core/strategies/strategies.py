from __future__ import annotations
import pandas as pd
from typing import Dict, Any
from .ai_models import AIUnifiedStrategy, list_models

class MACrossoverStrategy:
    name = "ma_crossover"
    def __init__(self, ma_fast: int = 20, ma_slow: int = 50):
        self.ma_fast = int(ma_fast)
        self.ma_slow = int(ma_slow)

    def generate_signal(self, df: pd.DataFrame) -> pd.Series:
        c = df['close']
        f = c.rolling(self.ma_fast).mean().ffill()
        s = c.rolling(self.ma_slow).mean().ffill()
        raw = (f > s).astype(float) * 2 - 1  # 1 or -1
        sig = pd.Series(raw.values, index=df.index, name='signal').fillna(0.0)
        return sig

class AIUnifiedWrapper:
    name = "ai_unified"
    def __init__(self, model_type: str = "random_forest", train_ratio: float = 0.7, threshold: float = 0.5, **kwargs):
        self.impl = AIUnifiedStrategy(model_type=model_type, train_ratio=train_ratio, threshold=threshold, **kwargs)

    def generate_signal(self, df: pd.DataFrame) -> pd.Series:
        return self.impl.generate_signal(df)

FAMILIES = {
    "conventional": ["ma_crossover"],
    "ai": ["ai_unified"],
    "hybrid": []
}

REGISTRY = {
    "ma_crossover": MACrossoverStrategy,
    "ai_unified": AIUnifiedWrapper
}

def list_strategies():
    return sorted(REGISTRY.keys())

def get_strategy_class(name: str):
    assert name in REGISTRY, f"Unknown strategy {name}"
    return REGISTRY[name]

def list_ai_models():
    return list_models()
