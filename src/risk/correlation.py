import pandas as pd, numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional
@dataclass
class CorrConfig:
    window: int = 126
    max_corr: float = 0.75
def rolling_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return np.log(prices).diff().dropna()
def compute_corr_matrix(rets: pd.DataFrame, window: int) -> pd.DataFrame:
    if len(rets) < max(2, window//2): return rets.corr()
    return rets.iloc[-window:].corr()
def violates_pairwise_cap(corr: pd.DataFrame, max_corr: float) -> bool:
    if corr.size == 0: return False
    c = corr.copy().abs(); np.fill_diagonal(c.values, 0.0)
    return bool((c.values > max_corr).any())
def marginal_corr_violation(existing_prices: pd.DataFrame, candidate_price: pd.Series, max_corr: float, window: int) -> Tuple[bool, Optional[float]]:
    if existing_prices is None or existing_prices.empty or candidate_price is None:
        return (False, None)
    df = existing_prices.join(candidate_price.rename("CAND"), how="inner")
    if df.shape[0] < 5: return (False, None)
    rets = rolling_returns(df); corr = compute_corr_matrix(rets, window=window)
    if "CAND" not in corr.columns: return (False, None)
    worst = float(np.nanmax(np.abs(corr.drop(index="CAND", columns="CAND").values))) if corr.shape[0] > 1 else 0.0
    return (bool(worst > max_corr), worst)
