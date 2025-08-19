
import logging
from core.bus.event_bus import event_bus
from core.events.data_events import FeaturesReady
from core.events.strategy_events import StrategySignalGenerated, SignalDirection
from strategies.strategy_factory import create

logger = logging.getLogger("StrategyService")

class StrategyService:
    def __init__(self, strategy_name: str):
        self.bus = event_bus
        self.strategy = create(strategy_name)
        self.bus.subscribe(FeaturesReady, self.on_features)
        logger.info(f"StrategyService initialized for {strategy_name}.")

    def on_features(self, e: FeaturesReady):
        row = e.features_row
        price = float(row.get('close', 0.0))
        s = self.strategy.signal_for_row(row)
        direction = SignalDirection.LONG if s > 0.05 else (SignalDirection.SHORT if s < -0.05 else SignalDirection.HOLD)
        self.bus.publish(StrategySignalGenerated(
            source="StrategyService",
            symbol=e.symbol,
            direction=direction,
            strength=float(s),
            price=price,
            info={'in_sample': e.in_sample}
        ))
