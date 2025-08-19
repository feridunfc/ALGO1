import pandas as pd
from typing import Dict, Union
try:
    from .engine import BacktestEngine as _Engine
except Exception:
    class _Engine:
        def run(self, data: pd.DataFrame, strategy):
            class Res:
                equity_curve = (1 + data['close'].pct_change().fillna(0)).cumprod()
                positions = pd.Series(0, index=data.index)
                trades = []
            return Res()
from ..risk.chain import RiskChain, PortfolioState, RiskDecision
DataLike = Union[pd.DataFrame, Dict[str, pd.DataFrame]]

class RiskExecutionAdapter:
    def __init__(self, sector_map: Dict[str,str] | None = None, primary_symbol: str = "ASSET"):
        self.engine = _Engine()
        self.risk = RiskChain()
        self.primary_symbol = primary_symbol
        self.sector_map = sector_map or {primary_symbol: "technology"}

    def _signals(self, strategy, df: pd.DataFrame) -> pd.Series:
        if hasattr(strategy, "generate_signals"):
            return strategy.generate_signals(df)
        elif hasattr(strategy, "predict_proba"):
            proba = strategy.predict_proba(df)
            s = proba.copy()*0
            s[proba>0.55] = 1
            s[proba<0.45] = -1
            return s
        else:
            return pd.Series(0, index=df.index)

    def run(self, data: DataLike, strategy):
        if isinstance(data, dict):
            closes = {sym: df['close'] for sym, df in data.items() if 'close' in df.columns}
            price_hist = pd.DataFrame(closes).dropna(how="any")
            for s in closes.keys(): self.sector_map.setdefault(s, "technology")
            portfolio = PortfolioState(price_history=price_hist, sector_map=self.sector_map)
            weights = {}
            for sym, df in data.items():
                if hasattr(strategy, "fit"): strategy.fit(df)
                raw = self._signals(strategy, df).astype(float)
                approved = []
                for ts, sig in raw.items():
                    dec: RiskDecision = self.risk.apply(sym, sig, portfolio)
                    approved.append(0.0 if not dec.ok else dec.weight)
                    portfolio.positions[sym] = approved[-1]
                weights[sym] = pd.Series(approved, index=df.index, name=f"w_{sym}")
            weights_df = pd.DataFrame(weights).reindex(price_hist.index).fillna(0.0)
            rets = price_hist.pct_change().shift(-1).fillna(0.0)
            port_ret = (weights_df * rets).sum(axis=1)
            equity = (1 + port_ret).cumprod()
            class Res:
                equity_curve = equity
                positions = weights_df
                trades = []
            return Res()
        else:
            df = data
            if hasattr(strategy, "fit"): strategy.fit(df)
            return self.engine.run(data=df, strategy=strategy)
