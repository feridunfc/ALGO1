def test_import_pages():
    import importlib
    for mod in ["streamlit_app", "pages.00_Home", "pages.01_Single_Run", "pages.02_Compare", "pages.03_HPO", "pages.04_History"]:
        importlib.import_module(mod)
