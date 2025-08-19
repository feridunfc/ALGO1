
from dataclasses import dataclass
import pandas as pd

@dataclass
class PortfolioUpdated:
    source: str
    equity_curve: pd.Series
