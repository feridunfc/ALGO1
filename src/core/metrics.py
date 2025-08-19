import numpy as np, pandas as pd
def sharpe_ratio(returns, risk_free=0.0, periods_per_year=252):
    r = pd.Series(returns).dropna()
    if r.empty: return 0.0
    excess = r - risk_free/periods_per_year
    mean = excess.mean() * periods_per_year
    sd = excess.std(ddof=1) * (periods_per_year**0.5)
    return float(mean/sd) if sd > 0 else 0.0

def sortino_ratio(returns, required_return=0.0, periods_per_year=252):
    r = pd.Series(returns).dropna()
    if r.empty: return 0.0
    downside = r[r < required_return]
    expected = r.mean() * periods_per_year
    down_stdev = downside.std(ddof=1) * (periods_per_year**0.5) if len(downside)>0 else 0.0
    return float(expected/down_stdev) if down_stdev>0 else 0.0

def max_drawdown(equity_curve):
    s = pd.Series(equity_curve).dropna()
    if s.empty: return 0.0
    peak = s.cummax()
    dd = ((peak - s) / peak).max()
    return float(dd)

def turnover(transactions):
    if not transactions: return 0.0
    return sum([abs(t.get('size',0) * t.get('price',0)) for t in transactions])
