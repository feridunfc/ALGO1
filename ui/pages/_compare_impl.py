import streamlit as st
import pandas as pd
from ui.services_ext.wf_hpo_runner_ext import run_wf_batch, run_hpo, list_strategies

def render():
    st.title("Strategy Compare — WF & HPO (No-Regression)")
    strategies = list_strategies()
    selected = st.multiselect("Stratejiler", strategies, default=strategies[:5] if strategies else [])
    c1, c2, c3 = st.columns(3)
    wf_splits = c1.number_input("WF splits", 2, 10, 5)
    wf_test = c2.number_input("Test days", 21, 252, 63)
    do_hpo = c3.checkbox("WF sonrası top-1 için HPO", value=False)

    if st.button("Run Compare"):
        with st.spinner("Running WF..."):
            table = run_wf_batch(selected, wf_splits=wf_splits, wf_test=wf_test)
        if table is None or table.empty:
            st.warning("No results. Make sure STRATEGY_REGISTRY is available or fixtures are present.")
            return
        st.subheader("WF Summary")
        st.dataframe(table.style.highlight_max(axis=0), use_container_width=True)
        st.download_button("Download CSV", data=table.to_csv().encode("utf-8"), file_name="wf_compare.csv", mime="text/csv")
        if do_hpo:
            top = table.sort_values("sharpe", ascending=False).head(1).index[0]
            st.info(f"HPO → {top}")
            res = run_hpo(top, n_trials=25)
            st.json(res)
