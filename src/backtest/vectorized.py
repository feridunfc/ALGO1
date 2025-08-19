
import numpy as np
import pandas as pd

def vectorized_pnl(df: pd.DataFrame, signals: pd.Series, commission=0.0005, slippage=0.0002):
    signals = signals.reindex(df.index).fillna(0.0)
    # execute at next open with slippage
    exec_price = df['open'] * (1 + slippage*np.sign(signals.shift(1).fillna(0)))
    ret = exec_price.pct_change().fillna(0.0) * signals.shift(1).fillna(0.0)
    trades = signals.diff().abs().fillna(0.0)
    ret -= trades * commission
    equity = (1 + ret).cumprod()
    return equity, ret
