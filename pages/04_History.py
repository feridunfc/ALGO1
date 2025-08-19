
import streamlit as st, os, json, sqlite3, pandas as pd
st.set_page_config(layout="wide", page_title="History", page_icon="📜")
st.title("📜 Geçmiş Sonuçlar")

base = "results"
runs = []
if os.path.isdir(base):
    for rid in sorted(os.listdir(base), reverse=True):
        p = os.path.join(base, rid, "report.json")
        if os.path.isfile(p):
            try:
                runs.append(json.loads(open(p,"r",encoding="utf-8").read()))
            except Exception:
                pass
if runs:
    df = pd.DataFrame(runs)
    st.dataframe(df, use_container_width=True, height=320)
else:
    st.info("Klasörde rapor bulunamadı.")

st.subheader("SQLite Kayıtları")
db = "results/results.db"
if os.path.isfile(db):
    with sqlite3.connect(db) as con:
        try:
            rdf = pd.read_sql_query("SELECT * FROM runs ORDER BY date DESC", con)
            st.dataframe(rdf, use_container_width=True, height=320)
        except Exception as e:
            st.warning(f"DB okunamadı: {e}")
        try:
            tdf = pd.read_sql_query("SELECT * FROM trades LIMIT 500", con)
            st.dataframe(tdf, use_container_width=True, height=320)
        except Exception:
            pass
else:
    st.caption("results.db bulunamadı (otomatik oluşturulur).")
