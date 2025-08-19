
import streamlit as st, os, json
st.set_page_config(layout="wide", page_title="Home", page_icon="🏠")
st.title("🏠 Ana Sayfa")
st.markdown("Profesyonel, modüler ve genişletilebilir algo-trading arayüzü. Soldaki **Pages** menüsünden odaları açın veya aşağıdan hızlı geçiş yapın.")

cols = st.columns(3)
with cols[0]:
    st.page_link("pages/01_Single_Run.py", label="🚀 Tekli Çalıştırma", icon="🚀")
with cols[1]:
    st.page_link("pages/02_Compare.py", label="⚖️ Strateji Karşılaştırma", icon="⚖️")
with cols[2]:
    st.page_link("pages/03_HPO.py", label="⚙️ Optimizasyon (HPO)", icon="⚙️")

st.subheader("Son 5 Deney")
base = "results"
rows = []
if os.path.isdir(base):
    for rid in sorted(os.listdir(base), reverse=True)[:5]:
        p = os.path.join(base, rid, "report.json")
        if os.path.isfile(p):
            try:
                rows.append(json.loads(open(p,"r",encoding="utf-8").read()))
            except Exception:
                pass
if rows:
    import pandas as pd
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
else:
    st.info("Henüz deney kaydı bulunamadı.")
