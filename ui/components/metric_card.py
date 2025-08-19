# ui/components/metric_card.py
from __future__ import annotations
import streamlit as st

def _call_st_metric(label, value, delta=None, help_text=None, label_visibility=None):
    """Streamlit sürüm farklarını güvenle tolere eden çağrı."""
    # Boş label erişilebilirlik uyarısını önle
    safe_label = label if (label and str(label).strip()) else "\u200b"  # zero-width space

    # Yeni sürümlerde label_visibility var; yoksa TypeError alırız → fallback
    try:
        if label_visibility is not None:
            st.metric(label=safe_label, value=value, delta=delta, help=help_text, label_visibility=label_visibility)
        else:
            st.metric(label=safe_label, value=value, delta=delta, help=help_text)
    except TypeError:
        # Eski Streamlit imzası: label_visibility yok
        try:
            st.metric(label=safe_label, value=value, delta=delta, help=help_text)
        except TypeError:
            # Çok eski sürümler: help bile olmayabilir
            try:
                st.metric(safe_label, value, delta)
            except Exception:
                # En son çare: basit yazdırma
                st.write(f"**{safe_label}**: {value}" + (f" ({delta})" if delta is not None else ""))

def metric_card(
    label: str,
    value,
    delta=None,
    help: str | None = None,
    label_visibility: str | None = None,
    **kwargs,   # fazladan gelen argümanları (icon, key vs.) yut
):
    """
    Güvenli metrik kartı.
    - Boş label uyarısını otomatik önler.
    - label_visibility sağlanırsa dener, desteklenmezse sessiz fallback yapar.
    - Fazladan argümanlar hata fırlatmaz (geriye dönük uyumluluk).
    """
    # Boş label gelirse otomatik gizlemeyi öner
    if (not label or str(label).strip() == "") and label_visibility is None:
        label_visibility = "collapsed"

    _call_st_metric(label=label, value=value, delta=delta, help_text=help, label_visibility=label_visibility)
