import streamlit as st
from ui.services_ext.wf_hpo_runner_ext import list_strategies, run_hpo

st.set_page_config(layout="wide", page_title="⚙️ Optimizasyon (HPO)", page_icon="⚙️")
st.title("⚙️ Optimizasyon (HPO)")

strategies = list_strategies()
key = st.selectbox("Optimize Edilecek Strateji", strategies)
trials = st.number_input("Deneme Sayısı (Trials)", 10, 500, 50)
metric = st.selectbox("Hedef Metrik", ["sharpe","win_rate"], index=0)
run_btn = st.button("Optimizasyonu Başlat", type="primary")

if run_btn:
    with st.spinner("Optuna çalışıyor..."):
        res = run_hpo(key, n_trials=int(trials), metric=metric)
    st.subheader("En İyi Parametreler")
    st.json(res.get("best_params", {}))
    st.subheader("En İyi Skor")
    st.metric("Hedef Metrik", f"{res.get('best_value',0.0):.4f}")
