
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from config.settings import Settings

def run():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    cfg = Settings.load(base)
    assert "binance" in cfg.exchanges
    assert cfg.symbols_map.get("BINANCE:BTCUSDT") == "BTC-USD"
    assert any(f.get("name")=="rsi_14" for f in cfg.features.get("indicators", []))
    print("config_load_ok")

if __name__ == "__main__":
    run()
