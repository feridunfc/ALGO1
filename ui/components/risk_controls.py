import streamlit as st, json
from pathlib import Path

RISK_CFG_PATH = Path("config/default_risk.json")

class RiskControlPanel:
    def render(self):
        with st.expander("Portfolio Constraints"):
            st.slider("Max Sector Exposure %", 1, 50, 20, key="ns_max_sector")
            st.slider("Max Correlation", 0.1, 1.0, 0.7, key="ns_max_corr")
            if st.button("Apply Constraints", key="ns_apply_constraints"):
                self._update_risk_config()

    def _update_risk_config(self):
        cfg = json.loads(RISK_CFG_PATH.read_text()) if RISK_CFG_PATH.exists() else {"risk_chain": {}}
        cfg["risk_chain"]["max_correlation"] = float(st.session_state.ns_max_corr)
        cfg["risk_chain"]["max_sector_exposure"] = float(st.session_state.ns_max_sector)/100.0
        RISK_CFG_PATH.write_text(json.dumps(cfg, indent=2))
        st.success("Risk config updated.")
