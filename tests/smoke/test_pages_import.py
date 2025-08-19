def test_pages_import():
    import importlib
    for mod in ["streamlit_app", "ui.pages.00_Home", "ui.pages.01_Single_Run", "ui.pages.02_Compare", "ui.pages.03_HPO", "ui.pages.04_History"]:
        importlib.import_module(mod)
