# tests/ui/conftest.py
# UI testlerine özel fixture ve ayarlar.
from __future__ import annotations
import os
import socket
import time
from urllib.parse import urlparse
import pytest


def _is_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _wait_until_up(url: str, retries: int = 20, sleep_s: float = 0.3) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    for _ in range(retries):
        if _is_port_open(host, port, timeout=0.5):
            return True
        time.sleep(sleep_s)
    return False


@pytest.fixture(scope="session")
def live_server() -> str:
    """
    UI adresi:
      - Env var ile: ALGO1_UI_URL
      - Yoksa varsayılan: http://127.0.0.1:8501
    Port kapalıysa testler SKIP edilir.
    """
    url = os.getenv("ALGO1_UI_URL", "http://127.0.0.1:8501")
    if not _wait_until_up(url):
        pytest.skip(f"UI sunucusu çalışmıyor (beklenen: {url}). "
                    f"Örnek: 'streamlit run src/ui/app.py --server.port 8501 --server.headless true'")
    return url


def pytest_configure(config):
    """
    'ui' marker'ını kaydederek PytestUnknownMarkWarning'i önler.
    (Alternatif olarak pyproject.toml içinde markers kısmına da ekleyebilirsin.)
    """
    config.addinivalue_line("markers", "ui: UI (Playwright) testleri")
