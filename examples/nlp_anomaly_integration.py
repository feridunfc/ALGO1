\
import asyncio
from datetime import datetime
import numpy as np
import pandas as pd

from src.nlp import SentimentAnalyzer, NewsFeeder
from src.anomaly import AnomalyDetector, AnomalyAlert, AnomalyType

class TradingMonitor:
    def __init__(self):
        self.sentiment = SentimentAnalyzer(model_type="financial")
        self.news_feeder = NewsFeeder({
            "rss_feeds": [
                "https://cointelegraph.com/rss",
                "https://news.bitcoin.com/feed/",
            ],
            "asset_keywords": {
                "BTC": ["Bitcoin", "BTC"],
                "ETH": ["Ethereum", "ETH"],
            },
        })
        self.anomaly_detector = AnomalyDetector({
            "sentiment": {"model": "isolation_forest", "params": {"contamination": 0.1}, "window": "6h"}
        })
        self.news_feeder.add_callback(self.handle_news)
        self.market_state = {"BTC": {"price": 0.0, "sentiment": 0.0}, "ETH": {"price": 0.0, "sentiment": 0.0}}

    async def start(self):
        self.news_feeder.start()
        asyncio.create_task(self._simulate_price_loop())
        while True:
            await asyncio.sleep(60)
            self._print_market_state()

    async def _simulate_price_loop(self):
        prices = {"BTC": 50000.0, "ETH": 3000.0}
        while True:
            for asset in prices:
                ch = np.random.normal(0, 0.01)
                if np.random.random() < 0.05:
                    ch = np.random.choice([-0.1, 0.1])
                prices[asset] *= (1 + ch)
                self.market_state[asset]["price"] = prices[asset]
                volume = float(np.random.lognormal(mean=10, sigma=0.5))
                self._check_price_anomaly(asset, prices[asset], volume)
            await asyncio.sleep(5)

    def _check_price_anomaly(self, asset: str, price: float, volume: float):
        df = pd.DataFrame([
            {"timestamp": datetime.utcnow(), "metric": "price", "value": price},
            {"timestamp": datetime.utcnow(), "metric": "volume", "value": volume},
        ])
        alerts = self.anomaly_detector.detect(df)
        for a in alerts:
            self._handle_alert(a)

    def handle_news(self, news):
        res = self.sentiment.analyze(news.content, source=news.source, asset=news.asset)
        if res and news.asset:
            self.market_state[news.asset]["sentiment"] = float(res.score)
            df = pd.DataFrame([{"timestamp": datetime.utcnow(), "metric": "sentiment", "value": float(res.score)}])
            for a in self.anomaly_detector.detect(df):
                self._handle_alert(a)

    def _handle_alert(self, alert: AnomalyAlert):
        tag = {AnomalyType.PRICE_SPIKE: "PRICE", AnomalyType.VOLUME_SURGE: "VOLUME", AnomalyType.SENTIMENT_SHIFT: "SENTIMENT"}.get(alert.anomaly_type, "ALERT")
        print(f"{tag} ALERT: {alert.description} | val={alert.value:.2f} sev={alert.severity:.2f}")
        if alert.severity > 0.7:
            self._risk_action(alert)

    def _risk_action(self, alert: AnomalyAlert):
        mapping = {
            AnomalyType.PRICE_SPIKE: "Tighten stop-loss",
            AnomalyType.VOLUME_SURGE: "Reduce size due to liquidity",
            AnomalyType.SENTIMENT_SHIFT: "Re-evaluate open positions",
        }
        print(f"RISK ACTION: {mapping.get(alert.anomaly_type, 'Review market')}")

    def _print_market_state(self):
        print("\n--- Market State ---")
        for asset, st in self.market_state.items():
            print(f"{asset}: Price={st['price']:.2f} | Sentiment={st['sentiment']:.2f}")

if __name__ == "__main__":
    monitor = TradingMonitor()
    asyncio.run(monitor.start())
