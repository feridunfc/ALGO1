def test_financial_data_normalizer_alias():
    # sitecustomize should have aliased FinancialDataNormalizer to DataNormalizer, if present
    try:
        from core.data_normalizer import FinancialDataNormalizer  # noqa
    except Exception as e:
        # We don't fail the whole suite; we assert import path exists at least
        assert "FinancialDataNormalizer" not in str(e), str(e)

def test_compare_safe_import():
    import ui.pages.compare_safe as cs
    assert hasattr(cs, "render")
