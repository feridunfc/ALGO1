
import os
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.skipif(not os.environ.get("LIVE_UI_URL"), reason="LIVE_UI_URL not set")

def test_backtest_button_click(page: Page, live_server):
    page.goto(f"{live_server}/")
    # Adapt selectors to your UI:
    page.click("#start-backtest")
    expect(page.locator("#loading-spinner")).to_be_visible()
    expect(page.locator("#results-table")).to_be_visible(timeout=15000)
