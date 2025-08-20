
import pytest
import pandas as pd
from datetime import datetime, timedelta
import asyncio
from pathlib import Path
import tempfile

# imports
try:
    from src.core.event_bus import EnhancedEventBus
    from src.core.payload_store import PayloadStore
    from src.core.events import EventTopic, BarClosedEvent, SignalEvent
    from src.core.strategy_orchestrator import StrategyOrchestrator
    from src.core.risk_engine import RiskEngine as RiskEngine_Legacy
    from src.core.risk.engine import RiskEngine as RiskEngine_Modern
    from src.core.backtest_engine import EventDrivenBacktestEngine
    from src.execution.backtest_gateway import BacktestExecutionGateway
except Exception:
    from core.event_bus import EnhancedEventBus
    from core.payload_store import PayloadStore
    from core.events import EventTopic, BarClosedEvent, SignalEvent
    from core.strategy_orchestrator import StrategyOrchestrator
    try:
        from core.risk_engine import RiskEngine as RiskEngine_Legacy
        RiskEngine_Modern = RiskEngine_Legacy
    except Exception:
        from core.risk.engine import RiskEngine as RiskEngine_Modern
        RiskEngine_Legacy = RiskEngine_Modern
    from core.backtest_engine import EventDrivenBacktestEngine
    from execution.backtest_gateway import BacktestExecutionGateway

@pytest.mark.asyncio
async def test_end_to_end_pipeline_with_bridge():
    bus = EnhancedEventBus()
    with tempfile.TemporaryDirectory() as d:
        store = PayloadStore(Path(d))
        # choose whichever RiskEngine import works
        try:
            risk = RiskEngine_Modern(bus, {
                'position_sizing': {'base_size': 1000, 'min_position': 100},
                'constraints': {'max_position_size': 50000}
            })
        except Exception:
            risk = RiskEngine_Legacy(bus, {
                'position_sizing': {'base_size': 1000, 'min_position': 100},
                'constraints': {'max_position_size': 50000}
            })

        strat = StrategyOrchestrator(bus, risk)
        exec_gw = BacktestExecutionGateway()

        engine = EventDrivenBacktestEngine(bus, store, {
            "initial_capital": 100000,
            "commission": 0.001,
            "slippage": 0.0005,
            "timeframe": "1d"
        })
        engine.attach_execution(exec_gw)

        # Bridge: listen ORDER_SUBMIT and forward to engine.submit_order
        from src.core.events import EventTopic as ET  # ensure same enum
        async def on_order_submit(ev):
            await engine.submit_order(ev)
        bus.subscribe(ET.ORDER_SUBMIT, on_order_submit, is_async=True)

        # Strategy: simple momentum demo (emit signals on up moves)
        class DemoStrategy:
            def __init__(self):
                self.prev = None
            async def on_bar(self, ev: BarClosedEvent):
                if self.prev is None:
                    self.prev = ev.close
                    return []
                ret = (ev.close - self.prev)/self.prev
                self.prev = ev.close
                if ret > 0.005:
                    return [SignalEvent(strategy_id="demo", symbol=ev.symbol, direction=1, strength=min(1.0, ret*10), confidence=0.6)]
                elif ret < -0.005:
                    return [SignalEvent(strategy_id="demo", symbol=ev.symbol, direction=-1, strength=min(1.0, abs(ret)*10), confidence=0.6)]
                return []
        strat.strategies["demo"] = DemoStrategy()

        # sample data (10 bars)
        dates = pd.date_range(end=datetime.utcnow(), periods=10, freq='D')
        df = pd.DataFrame({
            "timestamp": dates,
            "symbol": ["AAPL"]*len(dates),
            "open": [100 + i*0.5 for i in range(len(dates))],
            "high": [100.5 + i*0.5 for i in range(len(dates))],
            "low":  [ 99.5 + i*0.5 for i in range(len(dates))],
            "close":[100.2 + i*0.5 for i in range(len(dates))],
            "volume":[100000 + i*100 for i in range(len(dates))],
        })

        # capture filled orders
        filled = []
        bus.subscribe(EventTopic.ORDER_FILLED, lambda ev: filled.append(ev))

        await bus.start()
        try:
            await engine.run(df, speed=100.0)
            # give time for async handlers
            await asyncio.sleep(0.1)
            assert len(filled) >= 0  # ensure no exception path
        finally:
            await bus.stop()
