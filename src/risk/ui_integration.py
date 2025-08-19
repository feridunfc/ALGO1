# src/risk/ui_integration.py
import json
from pathlib import Path
import streamlit as st

CFG_PATH = Path("config/config.json")

class RiskControlUI:
    def render_controls(self):
        st.sidebar.header("Risk Ayarları")
        cfg = json.loads(CFG_PATH.read_text()) if CFG_PATH.exists() else {}

        # Sector limits
        sector_limits = cfg.get("SECTOR_LIMITS", {"technology":0.2})
        for sector, limit in list(sector_limits.items()):
            new_limit = st.sidebar.slider(f"{sector} Limit %", 0.0, 50.0, float(limit*100), key=f"risk_{sector}_limit")
            sector_limits[sector] = new_limit/100.0

        # Correlation
        max_corr = float(cfg.get("MAX_CORRELATION", 0.7))
        max_corr = st.sidebar.slider("Maksimum Korelasyon", 0.1, 1.0, max_corr, key="risk_max_correlation")

        cfg["SECTOR_LIMITS"] = sector_limits
        cfg["MAX_CORRELATION"] = max_corr
        if st.sidebar.button("Kaydet", key="risk_save_cfg"):
            CFG_PATH.write_text(json.dumps(cfg, indent=2))
            st.sidebar.success("Risk config güncellendi")
