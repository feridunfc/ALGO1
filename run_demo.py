import pandas as pd
from src.core.event_bus import EventBus
from src.data.normalizer import DataNormalizer
from src.core.backtest import BacktestEngine
from src.core.risk import RiskManager
from src.core.performance import PerformanceAnalyzer
from src.core.strategy_framework import StrategyBase, StrategyRegistry

# simple demo strategy
class SimpleMeanReversion(StrategyBase):
    def generate_signals(self, data: pd.DataFrame):
        close = data['close'] if 'close' in data.columns else data.iloc[:,0]
        z = (close - close.rolling(20).mean()) / (close.rolling(20).std().replace(0,1e-6))
        return -z  # short if z>0, long if z<0

def main():
    # load sample CSV if exists else create synthetic
    try:
        df = pd.read_csv('AAPL.csv', parse_dates=True, index_col=0)
    except Exception:
        idx = pd.date_range('2023-01-01', periods=100, freq='D')
        import numpy as np
        price = 100 + np.cumsum(np.random.randn(len(idx)))
        df = pd.DataFrame({'open':price, 'high':price*1.01, 'low':price*0.99, 'close':price}, index=idx)
    normalizer = DataNormalizer(nan_policy='ffill')
    nd = normalizer.normalize(df)
    price_data = {'AAPL': df}  # use raw price for execution logic
    risk = RiskManager(target_volatility=0.15)
    back = BacktestEngine(price_data, initial_capital=100000)
    strat = SimpleMeanReversion()
    sig = strat.generate_signals(nd)
    # convert series to signals mapping
    signals = {}
    for ts, v in sig.dropna().iteritems():
        # map signal to -1..1 scaled
        s = max(-1.0, min(1.0, float(v)))
        signals[ts] = [{'symbol':'AAPL','signal':s,'size_pct':0.01}]
    res = back.run_signals(signals)
    metrics = PerformanceAnalyzer.calculate_metrics(res['trade_log'], res['portfolio_history'])
    print('Metrics:', metrics)

if __name__ == '__main__':
    main()
