
import streamlit as st
from datetime import datetime
import pandas as pd
from ..configs.config_loader import load_config_from_yaml
from ..run_backtest import run_backtest_once
from ..services.reporting_service import ReportingService

def _sidebar_cfg():
    cfg = load_config_from_yaml(None)
    with st.sidebar:
        st.header("Config")
        cfg.data.symbol = st.text_input("Symbol", cfg.data.symbol)
        cfg.data.start = st.text_input("Start (YYYY-MM-DD)", cfg.data.start)
        cfg.data.end = st.text_input("End (YYYY-MM-DD or empty)", "" if cfg.data.end is None else cfg.data.end)
        cfg.data.interval = st.selectbox("Interval", ["1d","1h","1wk"], index=0)
        cfg.fees.commission = float(st.number_input("Commission", value=float(cfg.fees.commission), step=0.001, format="%.5f"))
        cfg.fees.slippage_bps = float(st.number_input("Slippage (bps)", value=float(cfg.fees.slippage_bps), step=1.0, format="%.0f"))
        st.subheader("Strategy")
        cfg.strategy_name = st.selectbox("Strategy", ["sma_crossover","ai_random_forest","ai_logreg"], index=0)
        cfg.params = {
            "ma_fast": int(st.number_input("MA Fast", value=20, step=1)),
            "ma_slow": int(st.number_input("MA Slow", value=50, step=1)),
        }
        cfg.risk.target_vol = float(st.number_input("Target Vol", value=0.15, step=0.01, format="%.2f"))
        cfg.risk.max_dd_pct = float(st.number_input("Max DD", value=0.30, step=0.05, format="%.2f"))
    if cfg.data.end == "":
        cfg.data.end = None
    return cfg

def show_main():
    st.title("Autonom ED v2.9.5 – Event Driven Backtests")
    tabs = st.tabs(["Data","Run","Compare","Report"])
    cfg = _sidebar_cfg()

    with tabs[0]:
        st.write("Parameters")
        st.json({
            "symbol": cfg.data.symbol, "start": cfg.data.start, "end": cfg.data.end,
            "interval": cfg.data.interval, "commission": cfg.fees.commission, "slippage_bps": cfg.fees.slippage_bps,
            "strategy": cfg.strategy_name, "params": cfg.params, "risk": {"target_vol": cfg.risk.target_vol, "max_dd_pct": cfg.risk.max_dd_pct}
        })

    with tabs[1]:
        st.subheader("Single Backtest")
        if st.button("Run Backtest"):
            try:
                df, metrics = run_backtest_once(cfg)
                if df is None or df.empty:
                    st.warning("No results.")
                else:
                    st.line_chart(df["equity"])
                    st.dataframe(pd.DataFrame([metrics]))
            except Exception as ex:
                st.error(f"Error: {ex}")

    with tabs[2]:
        st.subheader("Compare")
        picks = st.multiselect("Strategies", ["sma_crossover","ai_random_forest","ai_logreg"], default=["sma_crossover","ai_random_forest"])
        rows = []
        for sname in picks:
            cfg.strategy_name = sname
            try:
                df, met = run_backtest_once(cfg)
                if df is not None and not df.empty:
                    st.line_chart(df["equity"], height=200)
                    rows.append({"strategy": sname, **met})
            except Exception as ex:
                st.error(f"{sname}: {ex}")
        if rows:
            st.dataframe(pd.DataFrame(rows))

    with tabs[3]:
        st.subheader("Last Report")
        rep = ReportingService()
        df, met = rep.get_last_results()
        if df is not None and not df.empty:
            st.line_chart(df["equity"])
            st.dataframe(pd.DataFrame([met]))
        else:
            st.info("Run a backtest first.")
