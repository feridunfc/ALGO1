
import os
import sys
import asyncio
import pytest

# Ensure project root and src/ on sys.path
ROOT = os.path.abspath(os.getcwd())
SRC = os.path.join(ROOT, "src")
for p in (ROOT, SRC):
    if p not in sys.path:
        sys.path.insert(0, p)

# Asyncio mode (pytest-asyncio >=0.21 uses auto by default; keep explicit for safety)
def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark test as asyncio-compatible")

@pytest.fixture(scope="session")
def live_server():
    """Return live UI URL from env var LIVE_UI_URL. Skip UI tests if not set."""
    url = os.environ.get("LIVE_UI_URL")
    if not url:
        pytest.skip("LIVE_UI_URL not set; skipping UI tests")
    return url
