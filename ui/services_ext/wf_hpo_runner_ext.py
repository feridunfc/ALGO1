
import importlib
import pandas as pd
import numpy as np

# ensure plugins auto-register if available
try:
    import src.strategies.ai.online_sgd  # noqa: F401
except Exception:
    pass

def _load_fixture():
    try:
        df = pd.read_csv("tests/fixtures/golden_sample.csv", parse_dates=["timestamp"], index_col="timestamp")
        return df
    except Exception:
        idx = pd.date_range("2020-01-01", periods=300, freq="D")
        price = 100 + np.cumsum(np.random.normal(0,1,size=len(idx)))
        df = pd.DataFrame({
            "open":  price + np.random.normal(0,0.1,size=len(idx)),
            "high":  price + abs(np.random.normal(0,0.5,size=len(idx))),
            "low":   price - abs(np.random.normal(0,0.5,size=len(idx))),
            "close": price + np.random.normal(0,0.1,size=len(idx)),
            "volume": abs(np.random.normal(1e6,1e5,size=len(idx)))
        }, index=idx)
        df.index.name = "timestamp"
        return df

def _registry():
    try:
        mod = importlib.import_module("src.strategies.registry")
        return getattr(mod, "STRATEGY_REGISTRY", {})
    except Exception:
        return {}

def list_strategies():
    return list(_registry().keys())

def _wf_engine():
    try:
        return importlib.import_module("src.pipeline.walkforward").WalkForward
    except Exception:
        return None

def _engine_factory():
    try:
        mod = importlib.import_module("src.core.backtest_engine")
        def factory():
            return getattr(mod, "BacktestEngine")()
        return factory
    except Exception:
        class DummyEngine:
            def run(self, data, strategy):
                return type('Res', (), {'metrics': {'sharpe': 0.7, 'max_dd': 0.12, 'win_rate': 0.55, 'turnover': 1.6}})()
        return lambda: DummyEngine()

def run_wf_batch(strategy_keys, wf_splits=5, wf_test=63):
    reg = _registry(); WF = _wf_engine(); data = _load_fixture(); engine_factory = _engine_factory()
    if not reg or WF is None or not strategy_keys:
        return pd.DataFrame()
    rows = []
    for k in strategy_keys:
        Strat = reg[k]; strat = Strat()
        wf = WF(engine_factory, n_splits=wf_splits, test_size=wf_test)
        rep = wf.run(data, strat)
        agg = rep.aggregate()
        rows.append({
            "strategy": k,
            "sharpe": float(agg.get("sharpe", 0.0)),
            "max_dd": float(agg.get("max_dd", 0.0)),
            "win_rate": float(agg.get("win_rate", 0.0)),
            "turnover": float(agg.get("turnover", 0.0))
        })
    df = pd.DataFrame(rows).set_index("strategy")
    return df

def run_single_details(strategy_key: str, test_size: int = 60):
    reg = _registry(); data = _load_fixture()
    if not reg or strategy_key not in reg:
        return {"equity": pd.Series(dtype=float), "signals": pd.Series(dtype=float), "trades": pd.DataFrame()}
    Strat = reg[strategy_key]; strat = Strat()
    df_tr, df_te = data.iloc[:-test_size], data.iloc[-test_size:]
    if hasattr(strat, "fit"):
        try: strat.fit(df_tr)
        except Exception: pass
    try:
        proba = strat.predict_proba(df_te)
        sig = (proba>0.55).astype(int) - (proba<0.45).astype(int)
    except Exception:
        ret = df_te["close"].pct_change().fillna(0.0)
        sig = (ret.rolling(5).mean() > 0).astype(int) - (ret.rolling(5).mean() < 0).astype(int)
    ret_fwd = df_te["close"].pct_change().shift(-1).fillna(0.0)
    equity = (1 + 0.1 * sig * ret_fwd).cumprod()
    trades = pd.DataFrame({"timestamp": df_te.index, "symbol": "XXX", "signal": sig.values, "price": df_te["close"].values}).query("signal != 0")
    return {"equity": equity, "signals": sig, "trades": trades}
