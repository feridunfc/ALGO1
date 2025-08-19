import pandas as pd, numpy as np
from src.committee.asset_selector import AssetSelector, AssetSelectorConfig
from src.committee.regime_detector import MarketRegimeDetector
from src.committee.enhanced_risk_engine_adapter import EnhancedRiskEngineAdapter
from src.committee.portfolio_constructor import PortfolioConstructor, PCConfig
from src.committee.trade_executor import TradeExecutor
from src.committee.committee_orchestrator import CommitteeOrchestrator

def test_committee_basic():
    idx = pd.date_range("2022-01-01", periods=260, freq="B")
    syms = ["AAA","BBB","CCC","DDD"]
    rng = np.random.default_rng(1)
    close = pd.DataFrame({s: 100 + np.cumsum(rng.normal(0,1,len(idx))) for s in syms}, index=idx)
    adv = pd.Series({s: 1_000_000 for s in syms})
    sector = {"AAA":"X","BBB":"X","CCC":"Y","DDD":"Z"}

    selector = AssetSelector(close, liquidity=adv, sector_map=sector, cfg=AssetSelectorConfig(max_assets=3))
    bench = close.mean(axis=1)
    regdet = MarketRegimeDetector(bench)
    ere = EnhancedRiskEngineAdapter(engine=None)
    pc = PortfolioConstructor(sector_map=sector, cfg=PCConfig(max_allocation_per_asset=0.2, sector_limits={"X":0.3}, cash_floor=0.05))
    te = TradeExecutor()
    comm = CommitteeOrchestrator(selector, regdet, ere, pc, te)

    out = comm.run_once()
    assert isinstance(out["target"], dict)
    assert sum(out["target"].values()) <= 0.95 + 1e-6  # cash floor korundu
