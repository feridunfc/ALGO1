
import streamlit as st
import importlib
from ui.services_ext.wf_hpo_runner_ext import list_strategies
st.set_page_config(layout="wide", page_title="HPO", page_icon="⚙️")
st.title("⚙️ Optimizasyon (HPO)")

strategies = list_strategies()
if not strategies:
    st.error("STRATEGY_REGISTRY bulunamadı")
    st.stop()

strategy = st.selectbox("Strateji", strategies)
trials = st.number_input("Deneme Sayısı", 10, 1000, 50)
metric = st.selectbox("Hedef Metrik", ["economic","sharpe","win_rate","turnover"], index=0)

if st.button("HPO Başlat", type="primary"):
    try:
        reg = importlib.import_module("src.strategies.registry").STRATEGY_REGISTRY
        Strat = reg[strategy]
        from src.pipeline.walkforward import WalkForward
        from src.optimization.hpo_runner import HPORunner
        from ui.services_ext.wf_hpo_runner_ext import _engine_factory, _load_fixture
        wf_factory = lambda: WalkForward(_engine_factory(), n_splits=3, test_size=30)
        runner = HPORunner(wf_factory, reg, metric=metric)
        study = runner.optimize(strategy, _load_fixture(), n_trials=int(trials))
        st.success(f"Best value: {getattr(study,'best_value',0):.4f}")
        st.json(getattr(study,'best_params',{}))
    except Exception as e:
        st.error(f"HPO hatası: {e}")
