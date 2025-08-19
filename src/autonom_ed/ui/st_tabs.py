from datetime import datetime
import streamlit as st
import pandas as pd
import yaml
from pathlib import Path

from ..run_backtest import main as run_single
from ..run_walkforward import main as run_wf

CFG_PATH = Path(__file__).resolve().parents[2] / "configs" / "main_config.yaml"
OUT_DIR = Path(__file__).resolve().parents[2] / "out"
OUT_DIR.mkdir(exist_ok=True, parents=True)

@st.cache_data(show_spinner=False)
def load_cfg():
    return yaml.safe_load(open(CFG_PATH, "r", encoding="utf-8"))

def save_cfg(cfg):
    CFG_PATH.write_text(yaml.dump(cfg), encoding="utf-8")

def _sidebar():
    cfg = load_cfg()
    st.sidebar.header("Data")
    symbol = st.sidebar.text_input("Symbol", value=cfg["data"]["symbol"])
    start = st.sidebar.text_input("Start", value=cfg["data"]["start"])
    end = st.sidebar.text_input("End", value=cfg["data"]["end"])
    interval = st.sidebar.selectbox("Interval", ["1d","1h","1wk"], index=0)

    st.sidebar.header("Strategy")
    strat = st.sidebar.selectbox("Strategy", ["sma_crossover","rf","logreg","xgb","lgbm"], index=0)
    ma_fast = st.sidebar.number_input("MA Fast", value=float(cfg["strategy"]["params"].get("ma_fast",20.0)), step=1.0)
    ma_slow = st.sidebar.number_input("MA Slow", value=float(cfg["strategy"]["params"].get("ma_slow",50.0)), step=1.0)

    st.sidebar.header("Risk")
    tv = st.sidebar.number_input("Target Vol (ann.)", value=float(cfg["risk"]["target_vol_annual"]), step=0.01, format="%.2f")
    mdd = st.sidebar.number_input("Max DD", value=float(cfg["risk"]["max_dd"]), step=0.01, format="%.2f")

    cfg["data"]["symbol"] = symbol
    cfg["data"]["start"] = start
    cfg["data"]["end"] = end
    cfg["data"]["interval"] = interval
    cfg["strategy"]["name"] = strat
    cfg["strategy"]["params"]["ma_fast"] = int(ma_fast)
    cfg["strategy"]["params"]["ma_slow"] = int(ma_slow)
    cfg["risk"]["target_vol_annual"] = float(tv)
    cfg["risk"]["max_dd"] = float(mdd)
    return cfg

def show_main():
    st.title("Autonom ED v2.9.3 — Event-Driven Backtesting")
    tabs = st.tabs(["Data","Train","Run","Compare","Report"])

    with tabs[0]:
        st.subheader("Config")
        cfg = _sidebar()
        if st.button("Save Config"):
            save_cfg(cfg)
            st.success("Saved.")

    with tabs[1]:
        st.subheader("Train (placeholder)")
        st.info("AI modeller için offline eğitim UI'si burada. Şimdilik CLI veya kodla eğitin.")

    with tabs[2]:
        st.subheader("Run Backtest")
        if st.button("Run Single Backtest"):
            try:
                run_single()
                st.success("Backtest finished.")
            except Exception as e:
                st.error(f"Error: {e}")

        st.caption("Walk-forward: uses simple date splits to replay test slices.")
        if st.button("Run Walk-Forward"):
            try:
                run_wf()
                st.success("Walk-forward finished.")
            except Exception as e:
                st.error(f"Error: {e}")

    with tabs[3]:
        st.subheader("Compare")
        # show latest metrics for common strategies
        st.write("Load metrics from `out/metrics_*.csv`")
        rows = []
        if OUT_DIR.exists():
            for p in OUT_DIR.glob("metrics_*.csv"):
                df = pd.read_csv(p)
                if not df.empty:
                    parts = p.stem.split("_")
                    symbol = parts[1]
                    strat = "_".join(parts[2:])
                    row = {"symbol":symbol,"strategy":strat}
                    row.update({k:float(df.iloc[0][k]) for k in df.columns})
                    rows.append(row)
        if rows:
            st.dataframe(pd.DataFrame(rows).sort_values("Sharpe", ascending=False), use_container_width=True)
        else:
            st.info("No metrics yet. Run a backtest.")

    with tabs[4]:
        st.subheader("Report")
        if OUT_DIR.exists():
            eq_files = list(OUT_DIR.glob("equity_*.csv"))
            if eq_files:
                latest = max(eq_files, key=lambda p: p.stat().st_mtime)
                st.write(f"Latest equity: `{latest.name}`")
                df = pd.read_csv(latest, parse_dates=["timestamp"]).set_index("timestamp")
                st.line_chart(df["equity"])
            else:
                st.info("No equity files yet.")
        else:
            st.info("No out directory yet.")
