import streamlit as st
import pandas as pd
from ...src.experiments.tracking_v2 import list_runs

def render():
    st.title("History")
    runs = list_runs()
    if not runs:
        st.info("No runs yet.")
        return
    df = pd.DataFrame(runs)
    df['ts_start'] = pd.to_datetime(df['ts_start'], unit='s')
    df['ts_end'] = pd.to_datetime(df['ts_end'], unit='s')
    st.dataframe(df)
    sel = st.selectbox("Select run_id", options=df['run_id'].tolist())
    if sel:
        row = next(r for r in runs if r["run_id"] == sel)
        st.subheader("Params")
        st.json(row["params"])
        st.subheader("Metrics")
        st.json(row["metrics"])
