
import pytest
import asyncio

# Imports resilient to different layouts
try:
    from src.core.risk.engine import RiskEngine  # new layout
except Exception:
    try:
        from src.core.risk_engine import RiskEngine  # legacy layout
    except Exception:
        from core.risk_engine import RiskEngine

try:
    from src.core.events import SignalEvent
except Exception:
    from core.events import SignalEvent

@pytest.mark.asyncio
async def test_risk_approval_and_rejection():
    cfg = {
        'position_sizing': {'base_size': 1000, 'min_position': 10},
        'constraints': {'max_position_size': 500}
    }
    engine = RiskEngine(None, cfg)

    sig_ok = SignalEvent(strategy_id="s1", symbol="AAPL", direction=1, strength=0.3, confidence=0.9)
    sig_big = SignalEvent(strategy_id="s1", symbol="AAPL", direction=1, strength=1.0, confidence=0.9)

    # Some repos name it assess_signal_risk, others assess_risk
    if hasattr(engine, "assess_signal_risk"):
        ok = await engine.assess_signal_risk(sig_ok)
        big = await engine.assess_signal_risk(sig_big)
    else:
        ok = await engine.assess_risk(sig_ok)
        big = await engine.assess_risk(sig_big)

    assert getattr(ok, "approved", True) is True
    assert getattr(big, "approved", False) is False
