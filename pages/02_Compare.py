
import streamlit as st
import pandas as pd
from ui.components.metric_card import metric_card
from ui.services_ext.wf_hpo_runner_ext import list_strategies, run_wf_batch

st.set_page_config(layout="wide", page_title="Strategy Compare", page_icon="⚖️")
st.title("⚖️ Strategy Comparison")

strategies = list_strategies()
selected = st.multiselect("Select strategies", strategies, default=strategies[:5] if strategies else [])
c1, c2 = st.columns(2)
wf_splits = c1.number_input("WF Splits", 2, 10, 5)
wf_test = c2.number_input("Test Days", 21, 252, 63)

if st.button("Run Compare", type="primary"):
    table = run_wf_batch(selected, wf_splits=int(wf_splits), wf_test=int(wf_test))
    if table is None or table.empty:
        st.warning("No results.")
    else:
        df = table.copy()
        df["risk_efficiency"] = (df.get("return", pd.Series(0, index=df.index)) / (df["max_dd"].abs() + 1e-9)).fillna(0.0)
        df["ta_sharpe"] = df["sharpe"] / (1.0 + df["turnover"].abs())
        st.dataframe(df.style.highlight_max(axis=0), use_container_width=True)
        st.download_button("Download CSV", data=df.to_csv().encode("utf-8"), file_name="wf_compare.csv", mime="text/csv")
        best = df.sort_values("ta_sharpe", ascending=False).head(1)
        if not best.empty:
            metric_card("Best TA-Sharpe", f"{best['ta_sharpe'].iloc[0]:.3f}")
            metric_card("Best Sharpe", f"{best['sharpe'].iloc[0]:.3f}")
            metric_card("Best Win Rate", f"{best['win_rate'].iloc[0]:.1%}")
