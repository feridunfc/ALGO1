import numpy as np
import pandas as pd

def max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = (equity/peak - 1.0).min()
    return float(abs(dd))

def ann_return(equity: pd.Series, freq=252) -> float:
    if equity.empty:
        return 0.0
    total_ret = equity.iloc[-1]/equity.iloc[0] - 1.0
    years = max((equity.index[-1] - equity.index[0]).days/365.25, 1e-9)
    return float((1.0+total_ret)**(1/years) - 1.0)

def sharpe(returns: pd.Series, rf=0.0, freq=252) -> float:
    if returns.std() == 0 or returns.empty:
        return 0.0
    return float(np.sqrt(freq) * (returns.mean() - rf/freq) / returns.std(ddof=1))

def sortino(returns: pd.Series, rf=0.0, freq=252) -> float:
    downside = returns[returns < 0.0]
    if downside.std() == 0 or returns.empty:
        return 0.0
    return float(np.sqrt(freq) * (returns.mean() - rf/freq) / downside.std(ddof=1))

def calmar(equity: pd.Series, returns: pd.Series, freq=252) -> float:
    mdd = max_drawdown(equity)
    if mdd == 0.0:
        return 0.0
    cagr = ann_return(equity, freq=freq)
    return float(cagr / mdd)

def summarize(equity: pd.Series) -> dict:
    if equity.empty:
        return {"CAGR":0,"Sharpe":0,"Sortino":0,"MaxDD":0,"Calmar":0}
    rets = equity.pct_change().dropna()
    return {
        "CAGR": ann_return(equity),
        "Sharpe": sharpe(rets),
        "Sortino": sortino(rets),
        "MaxDD": max_drawdown(equity),
        "Calmar": calmar(equity, rets),
    }
