from typing import Dict

REQUIRED = {
    "position_sizing": ["kelly","vol_target"],
    "circuit_breakers": ["max_dd","daily_loss_limit"],
    "liquidity_checks": ["min_volume","max_position_%"]
}

class RiskChecks:
    @staticmethod
    def verify_risk_controls(config: Dict) -> Dict[str, bool]:
        implemented = {}
        rc = config.get("risk_controls", {})
        for cat, methods in REQUIRED.items():
            implemented[cat] = all(m in rc for m in methods)
        return implemented
