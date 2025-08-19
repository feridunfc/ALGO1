from dataclasses import dataclass
import pandas as pd, numpy as np, warnings, math
from typing import Dict, Any, List, Optional, Callable
from src.core.event_bus import EventBus

event_bus = EventBus()

@dataclass
class Trade:
    symbol: str
    entry_time: pd.Timestamp
    exit_time: Optional[pd.Timestamp]
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    direction: int
    commission: float
    slippage: float
    pnl: Optional[float]
    pnl_pct: Optional[float]

class BacktestEngine:
    def __init__(self, price_data: Dict[str, pd.DataFrame], initial_capital: float = 100000.0,
                 commission_model: Optional[Callable] = None, slippage_model: Optional[Callable] = None):
        self.price_data = price_data
        self.initial_capital = float(initial_capital)
        self.commission_model = commission_model or (lambda size: max(1.0, 0.0005 * size))
        self.slippage_model = slippage_model or (lambda size, vol: 0.0005 * vol)
        self.trade_log: List[Trade] = []
        self.portfolio = {'cash': self.initial_capital, 'positions': {}, 'value': self.initial_capital}
        self.portfolio_history = pd.Series([self.initial_capital])
        self._timestamps = sorted({idx for df in price_data.values() for idx in df.index})

    def _get_execution_price(self, symbol: str, timestamp: pd.Timestamp):
        df = self.price_data.get(symbol)
        if df is None:
            raise KeyError(symbol)
        try:
            pos = df.index.get_loc(timestamp) + 1
            if pos >= len(df):
                return None, None
            row = df.iloc[pos]
            return float(row['open']), row
        except KeyError:
            return None, None

    def execute_trade(self, symbol: str, signal: int, size_pct: float, timestamp: pd.Timestamp) -> Optional[Trade]:
        # get 1-bar delayed price
        exec_price, exec_row = self._get_execution_price(symbol, timestamp)
        if exec_price is None:
            return None
        vol = (exec_row.get('high', exec_price) - exec_row.get('low', exec_price)) / max(exec_price,1e-9)
        trade_value = self.portfolio['value'] * float(size_pct)
        slippage_pct = float(self.slippage_model(trade_value, vol))
        # direction: 1 buy, -1 sell
        direction = int(np.sign(signal)) if signal != 0 else 0
        if direction == 0:
            return None
        # adjust exec price by slippage in direction
        exec_price = exec_price * (1.0 + slippage_pct * direction)
        commission = float(self.commission_model(trade_value))
        qty = trade_value / exec_price if exec_price>0 else 0.0
        # apply commission
        self.portfolio['cash'] -= commission
        # update positions
        self.portfolio['positions'][symbol] = self.portfolio['positions'].get(symbol,0.0) + qty * direction
        trade = Trade(symbol=symbol, entry_time=timestamp, exit_time=None, entry_price=exec_price,
                      exit_price=None, quantity=qty, direction=direction, commission=commission,
                      slippage=slippage_pct*trade_value, pnl=None, pnl_pct=None)
        self.trade_log.append(trade)
        return trade

    def _mark_to_market(self, timestamp: pd.Timestamp):
        total = self.portfolio['cash']
        for sym, qty in self.portfolio['positions'].items():
            df = self.price_data.get(sym)
            if df is None: continue
            try:
                price = float(df.loc[timestamp]['close']) if timestamp in df.index else float(df.iloc[-1]['close'])
            except Exception:
                price = 0.0
            total += qty * price
        self.portfolio['value'] = total
        self.portfolio_history = self.portfolio_history.append(pd.Series([total]), ignore_index=True)
        return total

    def run_signals(self, signals: Dict[pd.Timestamp, List[Dict[str,Any]]]):
        # signals: mapping timestamp -> list of trades {symbol, signal, size_pct}
        for ts in sorted(signals.keys()):
            for s in signals[ts]:
                self.execute_trade(s['symbol'], s['signal'], s['size_pct'], ts)
            self._mark_to_market(ts)
        return {'final_value': self.portfolio['value'], 'trade_count': len(self.trade_log), 'trade_log': self.trade_log, 'portfolio_history': self.portfolio_history}

    def run_walk_forward(self, strategy_factory: Callable, n_splits: int = 3):
        from sklearn.model_selection import TimeSeriesSplit
        # build unified DataFrame of timestamps (assumes aligned index)
        all_idx = pd.Index(self._timestamps)
        tss = TimeSeriesSplit(n_splits=n_splits)
        results = []
        for fold, (train_idx, test_idx) in enumerate(tss.split(all_idx)):
            train_idx_dates = all_idx[train_idx]
            test_idx_dates = all_idx[test_idx]
            # create train and test mapped price_data (subset rows)
            train_price = {s: df.loc[df.index.isin(train_idx_dates)] for s, df in self.price_data.items()}
            test_price = {s: df.loc[df.index.isin(test_idx_dates)] for s, df in self.price_data.items()}
            strat = strategy_factory()
            try:
                strat.fit(pd.concat([df for df in train_price.values()])) if hasattr(strat, 'fit') else None
            except Exception:
                pass
            engine = BacktestEngine({**train_price, **test_price}, initial_capital=self.initial_capital,
                                    commission_model=self.commission_model, slippage_model=self.slippage_model)
            # build signals from strategy on combined DF per symbol (strategy must produce signals per timestamp)
            signals = {}
            # simplistic: call strategy.generate_signals on concatenated DF per symbol; user strategy must align
            combined = pd.concat([df for df in {**train_price, **test_price}.values()])
            # generate signals (strategy expected to return Series indexed by timestamps)
            sig_series = strat.generate_signals(combined)
            for ts, val in sig_series.dropna().iteritems():
                signals.setdefault(ts, []).append({'symbol': 'AAPL', 'signal': float(val), 'size_pct': 0.01})
            res = engine.run_signals(signals)
            res['fold'] = fold
            results.append(res)
        return results
