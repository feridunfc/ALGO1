
import os
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.skipif(not os.environ.get("LIVE_UI_URL"), reason="LIVE_UI_URL not set")

def test_event_log_updates(page: Page, live_server):
    page.goto(f"{live_server}/")
    page.click("#start-backtest")
    # Event log should receive a few lines during run
    expect(page.locator("#event-log")).to_contain_text("BarClosedEvent", timeout=20000)
    expect(page.locator("#event-log")).to_contain_text("SignalEvent")
    expect(page.locator("#event-log")).to_contain_text("OrderFilledEvent")
