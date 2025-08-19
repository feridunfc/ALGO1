import streamlit as st
import pandas as pd
from datetime import date, timedelta

from engines.data_loader import DataLoader
from engines.feature_engineer import make_features
from engines.signal_generator import vectorized_ma_signals
from backtest.vectorized import backtest_vectorized
from engines.metrics_engine import summarize
from risk.stress_test import StressTester

st.set_page_config(page_title="Autonom Trading v2.9.7 Hotfix", layout="wide")

def run_single(symbol: str, start: str, end: str, interval: str="1d"):
    df = DataLoader().load_yfinance(symbol, start, end, interval)
    feat = make_features(df)
    sig = vectorized_ma_signals(feat)
    bt = backtest_vectorized(df, sig, commission=0.0005, slippage_bps=1.0)
    stats = summarize(bt)
    return df, feat, sig, bt, stats

st.title("Autonom Trading — v2.9.7 Hotfix")
with st.sidebar:
    st.header("Controls")
    symbol = st.text_input("Symbol", "SPY")
    end_d = date.today()
    start_d = end_d - timedelta(days=365*3)
    start = st.date_input("Start", start_d)
    end = st.date_input("End", end_d)
    interval = st.selectbox("Interval", ["1d","1h","30m","15m"], index=0)
    run = st.button("Run Backtest")

tabs = st.tabs(["Data","Train","Run","Compare","Report","Stress"])

if run:
    df, feat, sig, bt, stats = run_single(symbol, str(start), str(end), interval)
    st.session_state["last"] = dict(df=df, feat=feat, sig=sig, bt=bt, stats=stats)

if "last" in st.session_state:
    last = st.session_state["last"]
    with tabs[0]:
        st.subheader("Data (first rows)")
        st.dataframe(last["df"].head())
    with tabs[1]:
        st.subheader("Features (tail)")
        st.dataframe(last["feat"].tail())
    with tabs[2]:
        st.subheader("Equity Curve")
        st.line_chart(last["bt"]["equity"])
    with tabs[3]:
        st.subheader("Signals (tail)")
        st.line_chart(last["sig"].tail(300))
    with tabs[4]:
        st.subheader("Metrics")
        st.json(last["stats"], expanded=False)
    with tabs[5]:
        st.subheader("Stress Tester")
        scenarios = {
            "Flash Crash": {symbol: -0.30},
            "Bear Shock": {symbol: -0.20},
            "Mild Shock": {symbol: -0.10}
        }
        if st.button("Run Stress Test"):
            equity = float(last["bt"]["equity"].iloc[-1]) * 100000.0
            portfolio = {symbol: equity}
            out = StressTester(scenarios).test(portfolio)
            st.table(pd.DataFrame(out).T)
else:
    with tabs[0]:
        st.info("Set parameters in the sidebar and click **Run Backtest**.")

st.caption("Walk-forward + event-driven replay live in services/backtesting_service.py — integrate into your pipeline as needed.")
