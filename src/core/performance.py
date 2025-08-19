import numpy as np, pandas as pd

class PerformanceAnalyzer:
    @staticmethod
    def calculate_metrics(trades, portfolio_values: pd.Series, risk_free_rate: float = 0.0):
        pv = pd.Series(portfolio_values).dropna().reset_index(drop=True)
        if pv.empty:
            return {}
        returns = pv.pct_change().dropna()
        total_return = (pv.iloc[-1] / pv.iloc[0]) - 1
        annualized_return = (1 + total_return) ** (252 / len(pv)) - 1 if len(pv)>0 else 0.0
        volatility = returns.std() * (252**0.5)
        downside_vol = returns[returns < 0].std() * (252**0.5) if len(returns[returns<0])>0 else 0.0
        max_dd = (pv / pv.cummax() - 1).min()
        winning = [t for t in trades if getattr(t, 'pnl', 0) and t.pnl>0]
        hit_ratio = len(winning) / len(trades) if trades else 0.0
        profit_factor = sum(t.pnl for t in winning) / abs(sum(t.pnl for t in trades if getattr(t,'pnl',0)<0)) if trades and any(getattr(t,'pnl',0)<0 for t in trades) else 0.0
        return {
            'sharpe_ratio': (annualized_return - risk_free_rate) / volatility if volatility>0 else 0.0,
            'sortino_ratio': (annualized_return - risk_free_rate) / downside_vol if downside_vol>0 else 0.0,
            'calmar_ratio': annualized_return / abs(max_dd) if max_dd!=0 else 0.0,
            'annualized_return': annualized_return,
            'max_drawdown': max_dd,
            'hit_ratio': hit_ratio,
            'profit_factor': profit_factor,
            'turnover': len(trades) / (len(pv)/252) if len(pv)>0 else 0.0
        }
