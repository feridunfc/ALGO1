from __future__ import annotations
import numpy as np, pandas as pd

def compute_metrics(equity: pd.Series, ret: pd.Series) -> dict:
    nav = equity / equity.iloc[0]
    rets = ret.fillna(0.0)
    ann_ret = (nav.iloc[-1]) ** (252 / max(len(nav), 1)) - 1 if len(nav) > 1 else 0.0
    ann_vol = rets.std() * np.sqrt(252) if rets.std() > 0 else 0.0
    sharpe = (rets.mean() * 252) / ann_vol if ann_vol > 0 else 0.0
    downside = rets[rets < 0]
    downside_vol = downside.std() * np.sqrt(252) if downside.std() > 0 else 0.0
    sortino = (rets.mean() * 252) / downside_vol if downside_vol > 0 else 0.0
    cum = (1 + rets).cumprod()
    peak = cum.cummax()
    dd = (cum / peak - 1.0).min()
    maxdd = float(dd) if np.isfinite(dd) else 0.0
    calmar = (ann_ret / abs(maxdd)) if maxdd < 0 else 0.0
    turnover = rets.abs().sum()
    return {"AnnReturn": float(ann_ret), "AnnVol": float(ann_vol), "Sharpe": float(sharpe),
            "Sortino": float(sortino), "MaxDD": float(maxdd), "Calmar": float(calmar),
            "Turnover": float(turnover), "FinalNAV": float(nav.iloc[-1]) if len(nav) else 1.0}
