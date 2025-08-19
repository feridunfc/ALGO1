import streamlit as st
import pandas as pd
from ..services.wf_hpo_runner import run_wf_batch, run_hpo
from ...src.strategies.registry import STRATEGY_REGISTRY

def render():
    st.title("Strategy Compare — WF & HPO")

    all_strats = list(STRATEGY_REGISTRY.keys())
    selected = st.multiselect("Select strategies to compare", options=all_strats, default=all_strats[:5])
    c1, c2, c3 = st.columns(3)
    with c1:
        wf_splits = st.number_input("WF splits", min_value=2, max_value=10, value=5, step=1)
    with c2:
        wf_test = st.number_input("Test size (days)", min_value=21, max_value=252, value=63, step=1)
    with c3:
        do_hpo = st.checkbox("Run HPO for top-1 after WF", value=False)

    if st.button("Run Compare"):
        with st.spinner("Running walk-forward on selected strategies..."):
            table = run_wf_batch(selected, wf_splits=wf_splits, wf_test=wf_test)
        st.subheader("WF Summary")
        st.dataframe(table.style.highlight_max(axis=0))

        csv = table.to_csv().encode("utf-8")
        st.download_button("Download CSV", data=csv, file_name="wf_compare.csv", mime="text/csv")

        if do_hpo:
            top = table.sort_values("sharpe", ascending=False).head(1).index[0]
            st.info(f"Running HPO for best strategy: {top}")
            res = run_hpo(top, n_trials=25)
            st.json(res)

if __name__ == "__main__":
    render()
