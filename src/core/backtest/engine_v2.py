"""Vectorized, multi-asset backtest engine with improved features.
- Accepts a dict of DataFrames per symbol, or a MultiIndex DataFrame.
- strategy_fn should accept (prices_dict, cfg) and return exposures dict or DataFrame of exposures per symbol in [-1,1].
- Supports percent-of-capital sizing, execution costs, ATR stops via AdvancedRisk, and portfolio aggregation.
- Returns structured result with per-symbol equity + portfolio metrics and drawdowns.
"""
import numpy as np
import pandas as pd
from copy import deepcopy
from datetime import timedelta
from ..risk.advanced import AdvancedRisk

def _to_panel(prices_input):
    # normalize input: if dict of dfs -> concat into wide-format with columns (symbol, field)
    if isinstance(prices_input, dict):
        dfs = {}
        for sym, df in prices_input.items():
            df2 = df.copy()
            df2.columns = pd.MultiIndex.from_product([[sym], df2.columns])
            dfs[sym] = df2
        panel = pd.concat(dfs.values(), axis=1)
        return panel
    elif isinstance(prices_input, pd.DataFrame):
        # assume MultiIndex columns or single symbol
        return prices_input
    else:
        raise ValueError('prices_input must be dict or DataFrame')

def compute_metrics(equity_series, freq='D'):
    s = equity_series.dropna().astype(float)
    returns = s.pct_change().dropna()
    if returns.empty:
        return {'total_return': float(s.iloc[-1]/s.iloc[0]-1) if len(s)>1 else 0.0}
    # annualization factor estimation
    ann = 252 if freq=='D' else 252
    mean = returns.mean()*ann
    vol = returns.std()*np.sqrt(ann)
    sharpe = mean / (vol + 1e-12)
    # Sortino
    negative = returns[returns<0]
    downside = negative.std()*np.sqrt(ann) if not negative.empty else 0.0
    sortino = mean / (downside + 1e-12)
    max_dd = (s / s.cummax() - 1).min()
    win_rate = (returns>0).mean()
    return {'total_return': float(s.iloc[-1]/s.iloc[0]-1),'sharpe':float(sharpe),'sortino':float(sortino),'max_drawdown':float(max_dd),'win_rate':float(win_rate)}

def run_vector_backtest(prices, strategy_fn, cfg=None, capital=100000.0, freq='D'):
    cfg = cfg or {}
    panel = _to_panel(prices)
    symbols = sorted({c[0] for c in panel.columns if isinstance(c, tuple)})
    # build per-symbol price frames
    price_dict = {sym: panel[sym].copy() for sym in symbols}
    # strategy exposures: expect dict {sym: series} or DataFrame with MultiIndex columns
    exposures = strategy_fn(price_dict, cfg)
    # normalize exposures to DataFrame aligned with index
    if isinstance(exposures, dict):
        exp_df = pd.DataFrame(exposures).reindex(panel.index).fillna(0.0)
    else:
        exp_df = exposures.reindex(panel.index).fillna(0.0)
    adv_risk = AdvancedRisk(cfg.get('risk', {}))
    # prepare results
    per_sym_equity = {}
    trades_all = []
    for sym in symbols:
        df = price_dict[sym].copy()
        if 'close' not in df.columns:
            raise ValueError(f"symbol {sym} missing close column")
        exp = exp_df.get(sym, pd.Series(0.0, index=df.index)).fillna(0.0)
        cash = capital * cfg.get('per_symbol_capital_frac', 1.0/len(symbols))
        position = 0.0
        equity_list = []
        atr = adv_risk.atr_from_df(df, lookback=cfg.get('atr_lookback',14))
        for ts, row in df.iterrows():
            price = row['close']
            target_pct = float(exp.loc[ts])
            desired_notional = target_pct * cash
            # determine units using percent-risk sizing
            atr_val = float(atr.loc[ts]) if ts in atr.index else None
            if cfg.get('risk',{}).get('use_atr', True) and atr_val and atr_val>0:
                units = adv_risk.position_size_percent_risk(price, atr_val, cash, pct_risk=cfg.get('risk',{}).get('pct_risk_per_trade',0.01), stop_multiplier=cfg.get('stop',{}).get('initial_pct',3.0))
            else:
                units = (desired_notional)/price if price>0 else 0.0
            delta = units - position
            if abs(delta) > 1e-9:
                # simplify costs
                fee = abs(delta*price) * cfg.get('execution',{}).get('fee_bps',0.0005)
                cash -= delta*price
                cash -= fee
                trades_all.append({'timestamp':ts,'symbol':sym,'size':delta,'price':price,'fee':fee})
                position = units
            mtm = cash + position*price
            equity_list.append({'timestamp':ts,'equity':mtm,'cash':cash,'position':position})
        per_sym_equity[sym] = pd.DataFrame(equity_list).set_index('timestamp')
    # portfolio aggregation (sum equities)
    all_idx = sorted(set().union(*[df.index for df in per_sym_equity.values()]))
    port_equity = None
    for sym, edf in per_sym_equity.items():
        s = edf['equity'].reindex(all_idx).ffill()
        if port_equity is None:
            port_equity = s
        else:
            port_equity = port_equity.add(s, fill_value=0.0)
    metrics = compute_metrics(port_equity, freq=freq)
    return {'per_symbol_equity':per_sym_equity,'portfolio_equity':port_equity,'trades':pd.DataFrame(trades_all),'metrics':metrics}
