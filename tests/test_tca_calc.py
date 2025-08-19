
import os, sys, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from execution.tca import implementation_shortfall

def test_is_buy_positive_when_worse_than_arrival():
    trades = pd.DataFrame({"qty":[1,1], "px":[101,102]})
    isf = implementation_shortfall(trades, arrival_price=100, side="BUY")
    assert isf > 0
