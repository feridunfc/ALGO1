
import os
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.skipif(not os.environ.get("LIVE_UI_URL"), reason="LIVE_UI_URL not set")

def test_risk_panel_visibility(page: Page, live_server):
    page.goto(f"{live_server}/")
    page.click("#toggle-risk-panel")
    expect(page.locator("#risk-panel")).to_be_visible()
    expect(page.locator("#risk-metrics")).to_contain_text("Value at Risk")
    page.click("#toggle-risk-panel")
    expect(page.locator("#risk-panel")).to_be_hidden()
