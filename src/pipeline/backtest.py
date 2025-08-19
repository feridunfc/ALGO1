import numpy as np, pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from typing import Dict

def _costs(sig: pd.Series, commission: float): return sig.diff().abs().fillna(0.0)*commission

def simple_backtest(df: pd.DataFrame, signals: pd.Series, fees) -> Dict:
    sig = signals.shift(1).fillna(0.0)
    ret = df['close'].pct_change().fillna(0.0)
    gross = sig*ret
    costs = _costs(sig, fees.commission)
    strat = gross - costs - (fees.slippage_bps/1e4)*abs(sig)
    eq = (1+strat).cumprod()
    return {'equity': eq, 'costs': costs}

def run_walkforward(df: pd.DataFrame, features: pd.DataFrame, signal_or_strategy, fees, n_splits:int=4, seed:int=42) -> Dict:
    tscv = TimeSeriesSplit(n_splits=n_splits)
    equity = pd.Series(1.0, index=df.index, name='equity')
    for tr, te in tscv.split(features):
        tr_sl = slice(tr[0], tr[-1]+1); te_sl = slice(te[0], te[-1]+1)
        if hasattr(signal_or_strategy, 'generate_signals'):
            sig_full = signal_or_strategy.generate_signals(df.iloc[tr_sl.start:te_sl.stop], features.iloc[tr_sl.start:te_sl.stop])
            sig = pd.Series(np.asarray(sig_full).ravel(), index=df.index[tr_sl.start:te_sl.stop]).loc[df.index[te_sl]].fillna(0.0)
        else:
            sig = signal_or_strategy.loc[df.index[te_sl]]
        bt = simple_backtest(df.loc[df.index[te_sl]], sig, fees)
        equity.loc[df.index[te_sl]] = (equity.iloc[tr_sl.stop-1] * bt['equity'] / bt['equity'].iloc[0]).values
    return {'equity': equity}
