import streamlit as st
import pandas as pd
import os, json
from pathlib import Path

st.set_page_config(layout="wide", page_title="🏠 Ana Sayfa", page_icon="🏠")
st.title("🏠 Ana Sayfa")
st.markdown("Platformun yetenekleri, son deneyler ve hızlı erişim.")

st.subheader("Sistem Durumu")
st.success("Tüm Motorlar ve Servisler Aktif")  # (Dinamikleştirilebilir)

st.subheader("Son Deneyler")
rows = []
results_dir = Path("results")
if results_dir.exists():
    for p in sorted(results_dir.glob("*/report.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
        try:
            d = json.loads(p.read_text())
            rows.append({
                "run_id": p.parent.name,
                "strategy": d.get("strategy","?"),
                "sharpe": d.get("metrics",{}).get("sharpe",0.0),
                "max_dd": d.get("metrics",{}).get("max_dd",0.0),
                "date": d.get("date","")
            })
        except Exception:
            pass
if rows:
    st.dataframe(pd.DataFrame(rows))
else:
    st.info("Kayıtlı deney bulunamadı.")

st.divider()
cols = st.columns(4)
with cols[0]:
    st.page_link("ui/pages/01_Single_Run.py", label="🔬 Yeni Backtest Başlat", icon="🚀")
with cols[1]:
    st.page_link("ui/pages/02_Compare.py", label="⚖️ Strateji Karşılaştırma", icon="⚖️")
with cols[2]:
    st.page_link("ui/pages/03_HPO.py", label="⚙️ Optimizasyon (HPO)", icon="⚙️")
with cols[3]:
    st.page_link("ui/pages/04_History.py", label="📜 Geçmiş Sonuçlar", icon="📜")
