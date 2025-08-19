
from dataclasses import dataclass
import pandas as pd

@dataclass
class WalkForwardConfig:
    train_len: int = 252
    test_len: int = 63
    step: int = None  # if None, equals test_len

def generate_walkforward_slices(df: pd.DataFrame, cfg: WalkForwardConfig):
    n = len(df)
    step = cfg.test_len if cfg.step is None else cfg.step
    i = 0
    while i + cfg.train_len + cfg.test_len <= n:
        train_idx = df.index[i:i+cfg.train_len]
        test_idx = df.index[i+cfg.train_len:i+cfg.train_len+cfg.test_len]
        yield train_idx, test_idx
        i += step
