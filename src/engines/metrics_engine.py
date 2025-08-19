
import numpy as np
import pandas as pd

class MetricsEngine:
    def __init__(self, rf=0.0):
        self.rf = rf  # annual risk-free

    def compute(self, equity_curve: pd.Series, returns: pd.Series):
        if len(returns.dropna()) < 2:
            return {}
        ann_mult = 252
        daily_rf = self.rf / ann_mult
        excess = returns - daily_rf
        sharpe = np.sqrt(ann_mult) * (excess.mean() / (excess.std() + 1e-12))
        downside = returns[returns < 0].std()
        sortino = np.sqrt(ann_mult) * (returns.mean() / (downside + 1e-12))
        cum = (1 + returns).cumprod()
        peak = cum.cummax()
        dd = (cum / peak - 1).min()
        ann_ret = cum.iloc[-1] ** (ann_mult / len(cum)) - 1
        ann_vol = returns.std() * np.sqrt(ann_mult)
        calmar = ann_ret / abs(dd) if dd < 0 else np.nan
        return {
            "ann_return": float(ann_ret),
            "ann_vol": float(ann_vol),
            "sharpe": float(sharpe),
            "sortino": float(sortino),
            "max_drawdown": float(dd),
            "calmar": float(calmar),
        }
