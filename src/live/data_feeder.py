
import threading, time, random
import pandas as pd

class MockMarketData:
    def __init__(self, symbols=None, update_sec: float = 1.0):
        self.symbols = symbols or ["AAPL","MSFT"]
        self.update_sec = update_sec
        self.callbacks = []

    def subscribe(self, callback):
        self.callbacks.append(callback)

    def start(self):
        def _run():
            price = {s: 100.0 + random.random()*10 for s in self.symbols}
            while True:
                for s in self.symbols:
                    price[s] = max(1e-3, price[s] * (1 + random.uniform(-0.002, 0.002)))
                    data = {
                        "symbol": s,
                        "price": price[s],
                        "volume": random.randint(1000, 10000),
                        "timestamp": pd.Timestamp.utcnow()
                    }
                    for cb in list(self.callbacks):
                        try: cb(data)
                        except Exception: pass
                time.sleep(self.update_sec)
        threading.Thread(target=_run, daemon=True).start()
