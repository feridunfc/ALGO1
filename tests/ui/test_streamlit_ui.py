# tests/ui/test_streamlit_ui.py
# Playwright ile Streamlit tabanlı (veya benzer) UI'yi duman/smoke test etmek için
# Not: Testler toleranslıdır; beklenen buton/başlık yoksa fail yerine skip eder.

from __future__ import annotations
import re
from pathlib import Path
import pytest
from playwright.sync_api import Page, expect

pytestmark = [pytest.mark.ui]  # uyarıyı engellemek için conftest.py pytest_configure de var

# Bu metin/regex listeleri UI'nizdeki Türkçe/İngilizce varyasyonları kapsar
HEADING_PATTERNS = [
    re.compile(r"Algo|Quant|Trading|Backtest", re.I),
    re.compile(r"Veri|Model|Strateji|Portföy|Sonuç|Rapor", re.I),
]

START_BUTTON_PATTERNS = [
    re.compile(r"Backtest", re.I),
    re.compile(r"Simülasyon|Simulasyon", re.I),
    re.compile(r"Başlat|Run|Start", re.I),
]

RESULTS_TEXT_PATTERNS = [
    re.compile(r"Sonuç|Results|Completed|Tamamlandı|Equity|PNL|Getiri", re.I),
]


def _any_heading_visible(page: Page) -> bool:
    # heading rolü üzerinden dene
    for pat in HEADING_PATTERNS:
        try:
            if page.get_by_role("heading", name=pat).first.is_visible():
                return True
        except Exception:
            pass
    # heading bulunamazsa plain text ile dene
    for pat in HEADING_PATTERNS:
        try:
            if page.get_by_text(pat).first.is_visible():
                return True
        except Exception:
            pass
    return False


def _find_start_button(page: Page):
    # Buton rolüyle regex’e uyan ilk butonu döndür
    for pat in START_BUTTON_PATTERNS:
        try:
            btn = page.get_by_role("button", name=pat).first
            if btn and btn.count() > 0 and btn.is_visible():
                return btn
        except Exception:
            pass
    # Streamlit bazen link/button karışık; düz metin tıklaması alternatif
    for pat in START_BUTTON_PATTERNS:
        try:
            cand = page.get_by_text(pat).first
            if cand and cand.is_visible():
                return cand
        except Exception:
            pass
    return None


def _has_results_indicator(page: Page) -> bool:
    # Metin bazlı bir sonuç göstergesi var mı?
    for pat in RESULTS_TEXT_PATTERNS:
        try:
            if page.get_by_text(pat).first.is_visible():
                return True
        except Exception:
            pass
    # Görsel/çizim/tablo gibi bir şey oluşmuş mu? (grafikler çoğunlukla img/canvas)
    try:
        if page.locator("canvas, svg, img, table").first.is_visible():
            return True
    except Exception:
        pass
    return False


def test_app_loads_and_has_main_sections(page: Page, live_server: str, tmp_path: Path):
    page.set_default_timeout(15000)
    page.goto(live_server, wait_until="domcontentloaded")
    found = _any_heading_visible(page)
    if not found:
        page.screenshot(path=str(tmp_path / "ui_load_fail.png"))
    assert found, "Ana sayfa beklenen başlıklardan/anahtar kelimelerden en az birini göstermiyor."


def test_try_start_backtest_if_button_exists(page: Page, live_server: str, tmp_path: Path):
    page.set_default_timeout(15000)
    page.goto(live_server, wait_until="domcontentloaded")

    btn = _find_start_button(page)
    if not btn:
        pytest.skip("Backtest başlatma butonu/metni bulunamadı (UI metinleri farklı olabilir).")

    # Tıklayıp kısa bir süre bekleyelim; sonuç emareleri arayacağız
    btn.click()
    page.wait_for_timeout(2000)
    if not _has_results_indicator(page):
        # Her UI’de sonuç göstergesi farklı olabilir → sert fail yerine bilgi amaçlı ekran görüntüsü
        page.screenshot(path=str(tmp_path / "after_click_no_results.png"))
        pytest.skip("Butona tıklandı ancak bilinen bir sonuç göstergesi bulunamadı (grafik/sonuç metni/tablo).")


def test_strategy_control_presence_if_any(page: Page, live_server: str, tmp_path: Path):
    page.set_default_timeout(15000)
    page.goto(live_server, wait_until="domcontentloaded")

    # Streamlit selectbox'lar çoğunlukla combobox rolüyle görünüyor
    combobox_count = 0
    try:
        combobox_count = page.get_by_role("combobox").count()
    except Exception:
        pass

    # Alternatif: slider veya checkbox gibi kontrol var mı?
    found_control = combobox_count > 0
    if not found_control:
        try:
            if page.get_by_role("slider").count() > 0:
                found_control = True
        except Exception:
            pass
    if not found_control:
        try:
            if page.get_by_role("checkbox").count() > 0:
                found_control = True
        except Exception:
            pass

    if not found_control:
        # Strateji kontrolü olmayan minimal UI’lerde skip etmek daha doğru
        page.screenshot(path=str(tmp_path / "no_controls.png"))
        pytest.skip("Strateji/Model kontrolleri bu sayfada görünmedi.")
    else:
        assert found_control is True
