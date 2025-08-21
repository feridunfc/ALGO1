import streamlit as st
from typing import Any
from src.strategies.registry import discover_strategies, get_param_schema, get_strategy_class

st.set_page_config(page_title="Strategy Console", layout="wide")

@st.cache_data(show_spinner=False)
def _discover():
    specs = discover_strategies()
    errs = getattr(discover_strategies, "errors", {})
    return specs, errs

def _render_param_form(schema: Any):
    if not schema or not hasattr(schema, "model_fields"):
        return {}
    vals = {}
    for name, field in schema.model_fields.items():
        ann = field.annotation
        default = field.default
        desc = getattr(field, "description", name)
        if ann in (int, "int"):
            vals[name] = st.number_input(desc, value=int(default) if default is not None else 0, step=1)
        elif ann in (float, "float"):
            vals[name] = st.number_input(desc, value=float(default) if default is not None else 0.0)
        elif ann in (bool, "bool"):
            vals[name] = st.checkbox(desc, value=bool(default) if default is not None else False)
        else:
            vals[name] = st.text_input(desc, value=str(default) if default is not None else "")
    return vals

def main():
    st.title("📊 Strategy Console")

    specs, errs = _discover()
    st.caption(f"{len(specs)} strateji bulundu.")
    if errs:
        with st.expander("Keşif sırasında atlanan modüller (log)"):
            for k, v in errs.items():
                st.code(f"{k}: {v}", language="text")

    # Ailelere göre gruplama
    by_family = {}
    for qn, s in specs.items():
        by_family.setdefault(s.family, []).append((qn, s))

    col_left, col_right = st.columns([2, 3])

    with col_left:
        fam = st.selectbox("Aile", sorted(by_family.keys()))
        options = {f"{s.display_name}  ·  ({s.module.split('.')[-1]})": qn for qn, s in sorted(by_family[fam], key=lambda x: x[1].display_name.lower())}
        label = st.selectbox("Strateji", list(options.keys()))
        qn = options[label]

        # Param şemasını yükle ve formu çiz
        ParamSchema = get_param_schema(qn)
        st.subheader("Parametreler")
        with st.form("param_form", clear_on_submit=False):
            params = _render_param_form(ParamSchema)
            run_clicked = st.form_submit_button("Çalıştır")

    with col_right:
        st.subheader("Özet")
        sel_spec = specs[qn]
        st.write(f"**Qualified name:** `{qn}`")
        st.write(f"**Family:** `{sel_spec.family}`")
        st.write(f"**Module:** `{sel_spec.module}`")

        if run_clicked:
            # Strateji sınıfını yükle ve örnek oluştur (params opsiyonel)
            StrategyClass = get_strategy_class(qn)
            try:
                instance = StrategyClass(params) if params else StrategyClass()  # her sınıfın init'i farklı olabilir
                st.success("Strateji örneği oluşturuldu.")
                st.json({"selected_strategy": sel_spec.display_name, "params": params})
                st.info("Backtest/raporlama entegrasyonu için sinyalleri üretip metriğe bağlayacağız.")
            except Exception as e:
                st.error(f"Örnek oluşturulamadı: {e}")

if __name__ == "__main__":
    main()
