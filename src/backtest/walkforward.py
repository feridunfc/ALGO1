from __future__ import annotations
import pandas as pd

def generate_walkforward_slices(df: pd.DataFrame, train: int=252, test: int=63):
    n = len(df)
    i = 0
    while i + train + test <= n:
        yield range(i, i+train), range(i+train, i+train+test)
        i += test
