
import logging
from core.bus.event_bus import event_bus
from core.events.data_events import BarDataEvent, FeaturesReady
from engines.feature_engineer_engine import FeatureEngineerEngine

logger = logging.getLogger("FeatureService")

class FeatureService:
    def __init__(self, feature_cfg=None):
        self.bus = event_bus
        self.engine = FeatureEngineerEngine(
            regime_params=(feature_cfg or {}).get('regime', {}).get('params', {}),
            anomaly_params=(feature_cfg or {}).get('anomaly', {}).get('params', {}),
        )
        self.in_sample = True
        self.symbol = None
        self.bus.subscribe(BarDataEvent, self.on_bar)
        logger.info("FeatureService initialized.")

    def reset(self, in_sample: bool, symbol: str):
        self.engine.reset()
        self.in_sample = in_sample
        self.symbol = symbol

    def on_bar(self, e: BarDataEvent):
        if self.symbol is not None and e.symbol != self.symbol:
            return
        row, tail = self.engine.update_with_bar({
            'index': e.index, 'open': e.open, 'high': e.high, 'low': e.low, 'close': e.close, 'volume': e.volume
        }, in_sample=self.in_sample)
        self.bus.publish(FeaturesReady(
            source="FeatureService",
            symbol=e.symbol,
            features_row=row,
            features_df_tail=tail,
            in_sample=self.in_sample
        ))
