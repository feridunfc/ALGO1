# module_10_shap_explainer.py
# pip install shap

import shap

def explain_trading_model(model, X, max_display=12):
    """Creates a SHAP explainer and returns the values. Plot as needed in your notebook/app."""
    try:
        explainer = shap.Explainer(model, X)
    except Exception:
        explainer = shap.KernelExplainer(model.predict, X[:50])
    shap_values = explainer(X)
    return shap_values
