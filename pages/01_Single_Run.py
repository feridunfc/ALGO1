
import streamlit as st, importlib
from ui.components.metric_card import metric_card
from ui.components.backend_console import render as console_render, log as console_log
from ui.components.charts import equity_curve_chart, drawdown_chart
from ui.services_ext.wf_hpo_runner_ext import list_strategies, run_wf_batch, run_single_details

st.set_page_config(layout="wide", page_title="🔬 Tekli Çalıştırma", page_icon="🔬")
st.title("🔬 Tekli Çalıştırma")

with st.sidebar:
    st.header("Veri & Risk")
    asset = st.selectbox("Varlık", ["AAPL","MSFT","BTC-USD"], index=0)
    interval = st.selectbox("Zaman Aralığı", ["1d","1h","15m"], index=0)
    commission = st.slider("Komisyon (bps)", 0, 50, 5)
    slippage = st.slider("Slippage (bps)", 0, 50, 5)

strategies = list_strategies()
if not strategies:
    st.error("STRATEGY_REGISTRY boş görünüyor. Lütfen strateji kayıtlarını kontrol edin.")
    console_render("Backend Console")
    st.stop()

key = st.selectbox("Strateji", strategies)

colL, colR = st.columns([1,2], gap="large")
with colL:
    st.subheader("Konfigürasyon")
    st.caption("Seçili stratejinin parametre formunu burada dinamikleştirebilirsiniz.")
    run = st.button("Backtest'i Çalıştır", type="primary", use_container_width=True)

with colR:
    if run:
        try:
            console_log("WF aggregate metrikler hesaplanıyor...", strategy=key)
            res = run_wf_batch([key], wf_splits=3, wf_test=30)
            sharpe = float(res.loc[key,"sharpe"]) if not res.empty else 0.0
            maxdd = float(res.loc[key,"max_dd"]) if not res.empty else 0.0
            winr  = float(res.loc[key,"win_rate"]) if not res.empty else 0.0
            metric_card("Sharpe", f"{sharpe:.2f}", label_visibility="visible")
            metric_card("Max DD", f"{maxdd:.1%}", label_visibility="visible")
            metric_card("Win Rate", f"{winr:.1%}", label_visibility="visible")

            console_log("Detaylı çıktı (equity, sinyal, trade) getiriliyor...", strategy=key)
            details = run_single_details(key, test_size=60)
            eq = details.get("equity")
            st.plotly_chart(equity_curve_chart(eq), use_container_width=True)
            st.plotly_chart(drawdown_chart(eq), use_container_width=True)

            with st.expander("İşlem Listesi (Trades)"):
                trades = details.get("trades")
                if trades is not None and not trades.empty:
                    st.dataframe(trades, use_container_width=True, height=260)
                else:
                    st.caption("Bu koşuda işlem oluşmadı veya veri mevcut değil.")
        except Exception as e:
            console_log(f"Backtest hatası: {e}", level="ERROR", strategy=key)
            st.error(f"Backtest hatası: {e}")

console_render("Backend Console")
