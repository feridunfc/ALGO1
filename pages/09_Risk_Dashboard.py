
import streamlit as st
import pandas as pd, numpy as np
from src.risk.reporting import RiskReporter

st.set_page_config(layout="wide", page_title="Risk Dashboard", page_icon="🛡️")
st.title("🛡️ Risk Analiz Paneli")

# Demo state provider
def _state():
    return {
        "positions": {"AAPL": 50, "MSFT": -30},
        "sector_map": {"AAPL":"TECH","MSFT":"TECH"},
        "last_prices": {"AAPL": 180.0, "MSFT": 340.0}
    }

reporter = RiskReporter(_state)
expo = reporter.sector_exposure()
st.subheader("Sektörel Dağılım")
st.bar_chart(pd.Series(expo))

st.subheader("VaR / CVaR (simüle)")
rets = pd.Series(np.random.normal(0.0005, 0.01, 252))
var, cvar = reporter.var_cvar(rets, alpha=0.95)
st.metric("VaR (95%)", f"{var:.2%}")
st.metric("CVaR (95%)", f"{cvar:.2%}")
