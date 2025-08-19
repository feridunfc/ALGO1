# ui/backtest_page.py
import traceback, json
import streamlit as st
import pandas as pd
from pathlib import Path

from ..src.backtest.wf_engine import WalkForwardEngine, BacktestEngine
from ..src.optimization.hpo_engine import HPOEngine
from ..src.strategies.xgboost_strategy import XGBoostStrategy
from ..src.risk.ui_integration import RiskControlUI

def _load_demo_data() -> pd.DataFrame:
    return pd.read_csv("tests/fixtures/golden_sample.csv", parse_dates=["timestamp"], index_col="timestamp")

class BacktestPage:
    def __init__(self):
        RiskControlUI().render_controls()
        self.mode = st.radio("Çalışma Modu", ["Tekli", "Walk-Forward", "HPO"], horizontal=True, key="ns_backtest_mode")
        if self.mode == "HPO":
            self._render_hpo_controls()
        else:
            self._render_standard_controls()

    def _render_hpo_controls(self):
        st.subheader("HPO")
        data = _load_demo_data()
        metric = st.selectbox("Optimizasyon Metriği", ["sharpe","winrate","maxdrawdown"], index=0, key="ns_hpo_metric")
        trials = st.number_input("Deneme Sayısı", 10, 1000, 50, key="ns_hpo_trials")
        if st.button("HPO Başlat", key="ns_run_hpo"):
            try:
                # persist chosen metric/trials
                cfg = json.loads(Path("config/config.json").read_text())
                cfg["HPO_METRIC"] = "sharpe"
                cfg["HPO_TRIALS"] = int(trials)
                Path("config/config.json").write_text(json.dumps(cfg, indent=2))
                study = HPOEngine().optimize(strategy_class=XGBoostStrategy, data=data)
                st.success(f"Best params: {study.best_params}")
            except Exception as e:
                st.error(f"HPO hatası: {str(e)}")
                st.session_state.ns_last_error = traceback.format_exc()

    def _render_standard_controls(self):
        data = _load_demo_data()
        if self.mode == "Walk-Forward":
            if st.button("Run WF", key="ns_run_wf"):
                rep = WalkForwardEngine(BacktestEngine).run(XGBoostStrategy(), data)
                st.dataframe(rep.to_frame())
                st.download_button("Download CSV", rep.to_frame().to_csv().encode(), "wf_results.csv")
        else:
            if st.button("Run Single", key="ns_run_single"):
                eng = BacktestEngine()
                res = eng.run(data, XGBoostStrategy())
                st.success("Done.")
                if hasattr(res, "equity_curve"):
                    st.line_chart(res.equity_curve)
