
import streamlit as st
from src.live.paper_engine import PaperExecutionSimulator
from src.live.data_feeder import MockMarketData
from src.core.slippage.volume_weighted import volume_weighted_slippage_bps

st.set_page_config(layout="wide", page_title="Paper Trading", page_icon="🧪")
st.title("🧪 Paper Trading (Simülasyon)")

symbols = st.multiselect("Semboller", ["AAPL","MSFT","BTC-USD"], default=["AAPL","MSFT"])
commission = st.slider("Komisyon (bps)", 0, 50, 5)
impact = st.slider("Impact factor", 0.01, 0.50, 0.10)

col1, col2 = st.columns(2)

if "paper_engine" not in st.session_state:
    st.session_state.paper_engine = PaperExecutionSimulator(initial_balance=100_000.0, commission_bps=commission)

if st.button("Veri Akışını Başlat"):
    md = MockMarketData(symbols=symbols, update_sec=1.0)
    def on_tick(t):
        # örnek strateji sinyali: rastgele buy/sell 0.1 lot
        import random
        side = "BUY" if random.random() > 0.5 else "SELL"
        qty = 0.1
        recent_volume = t["volume"]
        bps = volume_weighted_slippage_bps(qty, recent_volume, impact_factor=impact)
        st.session_state.paper_engine.submit_order(t["symbol"], side, qty, t["price"], slippage_bps=bps)
    md.subscribe(on_tick)
    md.start()
    st.success("Mock market data başlatıldı.")

with col1:
    st.subheader("Pozisyonlar / Nakit")
    st.json({"cash": st.session_state.paper_engine.cash, "positions": st.session_state.paper_engine.positions})

with col2:
    st.subheader("Son Fill'ler")
    rows = [f.__dict__ for f in st.session_state.paper_engine.fills[-20:]]
    if rows:
        import pandas as pd
        st.dataframe(pd.DataFrame(rows), use_container_width=True, height=300)
    else:
        st.caption("Henüz fill yok.")
