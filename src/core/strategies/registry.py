import numpy as np, pandas as pd
from typing import Dict, List

_REG: Dict[str, type] = {}

def register(name:str):
    def deco(cls): _REG[name]=cls; return cls
    return deco

def list_strategies()->List[str]: return sorted(_REG.keys())
def get_strategy(name:str, params:Dict): 
    if name not in _REG: raise ValueError(f'unknown strategy: {name}')
    return _REG[name](**(params or {}))

class BaseStrategy:
    def generate_signals(self, df: pd.DataFrame, features: pd.DataFrame) -> pd.Series: ...

@register("ma_crossover")
class MACrossover(BaseStrategy):
    def __init__(self, ma_fast:int=20, ma_slow:int=50):
        self.fast=ma_fast; self.slow=ma_slow
    def generate_signals(self, df, features):
        fast = df['close'].rolling(self.fast).mean()
        slow = df['close'].rolling(self.slow).mean()
        sig = np.sign((fast-slow).fillna(0.0))
        return pd.Series(sig, index=df.index, name='signal')

@register("ai_unified")
class AIUnified(BaseStrategy):
    def __init__(self, model_name:str='random_forest', threshold:float=0.5):
        from core.models.registry import get_model
        self.model = get_model(model_name); self.th = float(threshold)
    def _target(self, df: pd.DataFrame):
        y = df['close'].pct_change().shift(-1).fillna(0.0)
        return (y>0).astype(int)
    def generate_signals(self, df, features):
        X = features.fillna(0.0).astype(float); y = self._target(df)
        n = int(len(X)*0.7)
        self.model.fit(X.iloc[:n], y.iloc[:n])
        proba = self.model.predict_proba(X.iloc[n:])
        out = pd.Series(0.0, index=df.index, name='signal')
        out.iloc[n:] = np.where(proba>=self.th, 1.0, -1.0)
        return out
