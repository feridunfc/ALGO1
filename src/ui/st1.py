import streamlit as st
from datetime import datetime, timedelta
from autonom_ed.configs.main_config import AppConfig
from autonom_ed.run_backtest import run as run_bt

st.set_page_config(page_title="Autonom ED v2.9.6", layout="wide")

def sidebar_cfg():
    cfg = AppConfig()
    st.sidebar.header("Data")
    cfg.data.symbol = st.sidebar.text_input("Symbol", value=cfg.data.symbol)
    col1, col2 = st.sidebar.columns(2)
    with col1:
        cfg.data.start = st.sidebar.text_input("Start (YYYY-MM-DD)", value=cfg.data.start or "")
    with col2:
        cfg.data.end = st.sidebar.text_input("End (YYYY-MM-DD)", value=cfg.data.end or "")
    cfg.data.interval = st.sidebar.selectbox("Interval", ["1d","1h","30m","15m","5m"], index=0)

    st.sidebar.header("Strategies")
    available = ["sma_crossover","rsi_threshold","ai_logreg","ai_random_forest"]
    cfg.strategies.strategy_names = st.sidebar.multiselect("Select strategies", available, default=["sma_crossover"])

    st.sidebar.header("Features")
    cfg.features.sma_fast = int(st.sidebar.number_input("SMA Fast", value=float(cfg.features.sma_fast), step=1.0))
    cfg.features.sma_slow = int(st.sidebar.number_input("SMA Slow", value=float(cfg.features.sma_slow), step=1.0))
    cfg.features.rsi_period = int(st.sidebar.number_input("RSI Period", value=float(cfg.features.rsi_period), step=1.0))

    st.sidebar.header("Risk")
    cfg.risk.initial_cash = float(st.sidebar.number_input("Initial Cash", value=float(cfg.risk.initial_cash), step=1000.0))
    cfg.risk.max_weight_per_asset = float(st.sidebar.number_input("Max Weight per Asset", value=float(cfg.risk.max_weight_per_asset), step=0.05, format="%.2f"))
    cfg.risk.risk_per_trade_pct = float(st.sidebar.number_input("Risk per Trade %", value=float(cfg.risk.risk_per_trade_pct), step=0.005, format="%.3f"))
    cfg.risk.atr_multiplier = float(st.sidebar.number_input("ATR Multiplier", value=float(cfg.risk.atr_multiplier), step=0.5))
    cfg.risk.vol_target_annual = float(st.sidebar.number_input("Vol Target (annual)", value=float(cfg.risk.vol_target_annual), step=0.05, format="%.2f"))
    cfg.risk.max_drawdown_limit = float(st.sidebar.number_input("Max Drawdown Limit", value=float(cfg.risk.max_drawdown_limit), step=0.05, format="%.2f"))

    st.sidebar.header("Fees")
    cfg.fees.commission = float(st.sidebar.number_input("Commission (as fraction)", value=float(cfg.fees.commission), step=0.0001, format="%.4f"))
    cfg.fees.slippage_bps = float(st.sidebar.number_input("Slippage (bps)", value=float(cfg.fees.slippage_bps), step=1.0))

    return cfg

tabs = st.tabs(["Data", "Run", "Compare", "Report"])

with tabs[0]:
    st.markdown("### Data")
    st.info("Veri kaynakları: yfinance (auto_adjust). UI bu örnekte sadece backtest tetikler; ayrıntılı grafikler bir sonraki sürümde.")

with tabs[1]:
    st.markdown("### Run Backtest")
    cfg = sidebar_cfg()
    if st.button("Run Backtest"):
        try:
            run_bt(cfg)
            st.success("Backtest tetiklendi. Çıktılar Streamlit console ve terminal log'larında.")
        except Exception as e:
            st.error(f"Backtest hata: {e}")

with tabs[2]:
    st.markdown("### Compare")
    st.info("Çoklu strateji metrik karşılaştırma tablosu—raporlama servisinden toplanan metriklerle doldurulacak.")

with tabs[3]:
    st.markdown("### Report")
    st.info("Raporlama servisi terminale metrikleri yazdırır. UI entegrasyonu bir sonraki sürümde tablolaşacak.")
