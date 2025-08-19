from dataclasses import dataclass, field
from typing import Dict, Optional
import json
from pathlib import Path
import pandas as pd
from .position_sizer import VolSizerConfig, realized_vol, volatility_scaled_weight, atr
from .correlation import CorrConfig, rolling_returns, compute_corr_matrix, violates_pairwise_cap, marginal_corr_violation

CFG_PATH = Path("config/config.json")
CFG = json.loads(CFG_PATH.read_text()) if CFG_PATH.exists() else {}

@dataclass
class PortfolioState:
    cash: float = 1_000_000.0
    positions: Dict[str, float] = field(default_factory=dict)
    sector_map: Dict[str, str] = field(default_factory=dict)
    price_history: Optional[pd.DataFrame] = None

class RiskDecision:
    def __init__(self, ok: bool, reason: str = "", weight: float = 0.0):
        self.ok = ok; self.reason = reason; self.weight = weight
    @staticmethod
    def approve(weight: float) -> "RiskDecision": return RiskDecision(True, "", weight)
    @staticmethod
    def reject(reason: str) -> "RiskDecision": return RiskDecision(False, reason, 0.0)

class CorrelationValidator:
    def __init__(self, max_corr: float, window: int):
        self.cfg = CorrConfig(window=window, max_corr=max_corr)
    def validate(self, symbol: str, new_weight: float, portfolio: PortfolioState) -> RiskDecision:
        ph = portfolio.price_history
        if ph is None or symbol not in ph.columns or len(ph) < 5:
            return RiskDecision.approve(new_weight)
        invested = [s for s,w in portfolio.positions.items() if abs(w)>1e-9 and s in ph.columns and s!=symbol]
        if invested:
            existing = ph[invested]; cand = ph[symbol]
            viol, worst = marginal_corr_violation(existing, cand, self.cfg.max_corr, self.cfg.window)
            if viol: return RiskDecision.reject(f"marginal_corr>{self.cfg.max_corr} (max={worst:.2f})")
        rets = rolling_returns(ph[sorted(ph.columns.unique())])
        corr = compute_corr_matrix(rets, window=self.cfg.window)
        if violates_pairwise_cap(corr, self.cfg.max_corr):
            return RiskDecision.reject(f"corr_cap>{self.cfg.max_corr}")
        return RiskDecision.approve(new_weight)

class PositionSizer:
    def __init__(self, vol_target: float, max_weight: float, lookback: int = 20, atr_n: int = 14):
        self.cfg = VolSizerConfig(vol_target=vol_target, max_weight=max_weight, lookback=lookback, atr_n=atr_n)
    def size(self, symbol: str, signal: float, portfolio: PortfolioState) -> float:
        if portfolio.price_history is not None and symbol in portfolio.price_history.columns:
            prices = portfolio.price_history[symbol]; rets = prices.pct_change()
        else:
            rets = pd.Series([0.0])
        vol_series = realized_vol(rets, n=self.cfg.lookback)
        return volatility_scaled_weight(signal, vol_series, self.cfg)

class RiskChain:
    def __init__(self):
        self.sector_limits: Dict[str, float] = CFG.get("SECTOR_LIMITS", {"technology":0.3})
        self.corr_validator = CorrelationValidator(max_corr=float(CFG.get("MAX_CORRELATION",0.75)), window=int(CFG.get("CORR_WINDOW",126)))
        self.sizer = PositionSizer(vol_target=float(CFG.get("VOL_TARGET",0.01)), max_weight=float(CFG.get("MAX_WEIGHT",0.25)))

    def apply(self, symbol: str, raw_signal: float, portfolio: PortfolioState) -> RiskDecision:
        sized = self.sizer.size(symbol, raw_signal, portfolio)
        sec = portfolio.sector_map.get(symbol, "unknown")
        sec_total = sum(abs(w) for s,w in portfolio.positions.items() if portfolio.sector_map.get(s,"unknown")==sec and s!=symbol)
        if sec in self.sector_limits and sec_total + abs(sized) > self.sector_limits[sec] + 1e-9:
            return RiskDecision.reject(f"sector_cap:{sec}>{self.sector_limits[sec]}")
        dec = self.corr_validator.validate(symbol, sized, portfolio)
        if not dec.ok: return dec
        return RiskDecision.approve(dec.weight)
