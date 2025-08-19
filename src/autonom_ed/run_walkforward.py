from .utils.logging_config import setup_logging
from .services.data_service import DataService
from .services.feature_service import FeatureService
from .services.strategy_service import StrategyService
from .services.risk_service import RiskService
from .services.execution_service import ExecutionService
from .services.portfolio_service import PortfolioService
from .services.backtest_service import BacktestingService
from .services.reporting_service import ReportingService
from .services.walkforward_service import WalkForwardService
from .core.bus.event_bus import event_bus
from datetime import datetime
import yaml
from pathlib import Path

def main(config_path=None):
    setup_logging()
    cfgp = Path(config_path or Path(__file__).resolve().parents[2] / "configs" / "main_config.yaml")
    cfg = yaml.safe_load(open(cfgp, "r", encoding="utf-8"))

    # services
    _ = DataService()
    _ = FeatureService(ma_fast=cfg["strategy"]["params"].get("ma_fast",20),
                       ma_slow=cfg["strategy"]["params"].get("ma_slow",50))
    _ = StrategyService(strategy_name=cfg["strategy"]["name"], params=cfg)
    _ = RiskService(target_vol_annual=cfg["risk"]["target_vol_annual"],
                    max_dd=cfg["risk"]["max_dd"])
    _ = ExecutionService()
    _ = PortfolioService(starting_equity=100000.0)
    _ = ReportingService()
    _ = BacktestingService()

    wf = WalkForwardService(n_splits=cfg["walkforward"]["n_splits"],
                            embargo_days=cfg["walkforward"]["embargo_days"])
    wf.run(symbol=cfg["data"]["symbol"],
           start=cfg["data"]["start"], end=cfg["data"]["end"],
           interval=cfg["data"]["interval"], strategy_name=cfg["strategy"]["name"])

if __name__ == "__main__":
    main()
