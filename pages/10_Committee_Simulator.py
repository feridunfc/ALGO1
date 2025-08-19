import streamlit as st
import pandas as pd, numpy as np
from src.committee.asset_selector import AssetSelector, AssetSelectorConfig
from src.committee.regime_detector import MarketRegimeDetector
from src.committee.enhanced_risk_engine_adapter import EnhancedRiskEngineAdapter
from src.committee.portfolio_constructor import PortfolioConstructor, PCConfig
from src.committee.trade_executor import TradeExecutor
from src.committee.committee_orchestrator import CommitteeOrchestrator, CommitteeConfig

st.set_page_config(layout="wide", page_title="Yatırım Komitesi Simülasyonu", page_icon="🧩")
st.title("🧩 Yatırım Komitesi Simülasyonu")

# Demo veri (repo verileri bağlı değilse)
idx = pd.date_range("2021-01-01", periods=500, freq="B")
syms = ["AAPL","MSFT","XOM","JPM","GLD"]
rng = np.random.default_rng(42)
close = pd.DataFrame({s: 100 + np.cumsum(rng.normal(0,1,len(idx))) for s in syms}, index=idx)
sector = {"AAPL":"TECH","MSFT":"TECH","XOM":"ENERGY","JPM":"FIN","GLD":"ALT"}
adv = pd.Series({s: 1_000_000 for s in syms})

st.sidebar.header("Parametreler")
max_assets = st.sidebar.slider("Maks. Varlık", 1, len(syms), 4)
max_per_asset = st.sidebar.slider("Varlık Başına Üst Sınır (%)", 1, 50, 10) / 100
tech_cap = st.sidebar.slider("TECH Sektör Üst Sınır (%)", 1, 80, 30) / 100
cash_floor = st.sidebar.slider("Nakit Alt Sınır (%)", 0, 50, 5) / 100

selector = AssetSelector(close, liquidity=adv, sector_map=sector,
                         cfg=AssetSelectorConfig(max_assets=max_assets))
bench = close.mean(axis=1)
regdet = MarketRegimeDetector(bench)
ere = EnhancedRiskEngineAdapter(engine=None)  # gerçek ERE'yi burada ver
pc = PortfolioConstructor(sector_map=sector,
                          cfg=PCConfig(max_allocation_per_asset=max_per_asset,
                                       sector_limits={"TECH": tech_cap},
                                       cash_floor=cash_floor))
te = TradeExecutor()
committee = CommitteeOrchestrator(selector, regdet, ere, pc, te,
                                  cfg=CommitteeConfig(regime_overrides={"crisis":{"max_allocation_per_asset": max_per_asset/2}}))

if st.button("Komiteyi Çalıştır", type="primary", use_container_width=True):
    out = committee.run_once(feature_provider=lambda s: {}, current_weights={})
    st.subheader("Rejim")
    st.code(out["regime"])
    st.subheader("Evren")
    st.write(out["universe"])
    st.subheader("Hedef Portföy")
    st.dataframe(pd.Series(out["target"]).rename("weight"))
    st.subheader("Emirler")
    st.dataframe(pd.DataFrame(out["orders"]))
else:
    st.info("Parametreleri ayarla ve **Komiteyi Çalıştır** butonuna tıkla.")
