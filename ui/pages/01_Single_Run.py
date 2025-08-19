import streamlit as st
import pandas as pd
import importlib
from ui.components.metric_card import metric_card
from ui.components.charts import equity_curve_chart, drawdown_chart


st.set_page_config(layout="wide", page_title="🔬 Tekli Çalıştırma", page_icon="🔬")
st.title("🔬 Tekli Çalıştırma")

from src.strategies.registry import STRATEGY_REGISTRY

strategies = sorted(list(STRATEGY_REGISTRY.keys()))
if not strategies:
    st.error("STRATEGY_REGISTRY boş. Lütfen kayıt bootstrapping'i kontrol edin.")
else:
    chosen = st.selectbox("Strateji", strategies)


# --- Sidebar: global data/risk controls (placeholder) ---
with st.sidebar:
    st.header("Veri & Risk")
    asset = st.selectbox("Varlık", ["AAPL","MSFT","BTC-USD"], index=0)
    interval = st.selectbox("Zaman Aralığı", ["1d","1h","15m"], index=0)
    commission = st.slider("Komisyon (bps)", 0, 50, 5)
    slippage = st.slider("Slippage (bps)", 0, 50, 5)

# Strategy registry
def list_strategies():
    try:
        mod = importlib.import_module("src.strategies.registry")
        return list(getattr(mod, "STRATEGY_REGISTRY", {}).keys())
    except Exception:
        return ["rb_ma_crossover"]
def get_strategy(key: str):
    mod = importlib.import_module("src.strategies.registry")
    return getattr(mod, "STRATEGY_REGISTRY")[key]

colL, colR = st.columns([1,2], gap="large")
with colL:
    st.subheader("Strateji Konfigürasyonu")
    strategies = list_strategies()
    key = st.selectbox("Strateji", strategies)
    params = {}
    # Dynamic param demo (extend by reading Strategy.suggest_params or signature)
    if "ma" in key:
        params["fast"] = st.number_input("Kısa Pencere", 3, 100, 10)
        params["slow"] = st.number_input("Uzun Pencere", 10, 300, 50)
    if "breakout" in key:
        params["lookback"] = st.number_input("Lookback", 5, 120, 20)

    st.expander("Risk Ayarları").write("max_open_positions, risk_per_trade_pct ... (projeye bağlayın)")

    run = st.button("Backtest'i Çalıştır", type="primary", use_container_width=True)

with colR:
    if run:
        try:
            # Use project's runner if available, else simple proxy
            try:
                Runner = importlib.import_module("ui.services.wf_hpo_runner").run_wf_for_strategy
                # We'll call with 1 split / 1 test to get a quick result
                table = importlib.import_module("ui.services.wf_hpo_runner").run_wf_batch([key], wf_splits=3, wf_test=30)
                sharpe = float(table.loc[key, "sharpe"])
                maxdd = float(table.loc[key, "max_dd"])
                winr  = float(table.loc[key, "win_rate"])
            except Exception:
                from ui.services_ext.wf_hpo_runner_ext import run_wf_batch
                table = run_wf_batch([key], wf_splits=3, wf_test=30)
                sharpe = float(table.loc[key, "sharpe"]) if not table.empty else 0.0
                maxdd = float(table.loc[key, "max_dd"]) if not table.empty else 0.0
                winr  = float(table.loc[key, "win_rate"]) if not table.empty else 0.0

            m1, m2, m3 = st.columns(3)
            metric_card("Sharpe", f"{sharpe:.2f}")
            metric_card("Max DD", f"{maxdd:.1%}")
            metric_card("Win Rate", f"{winr:.1%}")
            st.info("Detaylı işlem/eküri eğrisi grafikleri, proje BacktestEngine sonuçlarına bağlanarak doldurulabilir.")
        except Exception as e:
            st.error(f"Backtest hatası: {e}")
