
import os, sys, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from data_layer.quality import data_quality_report

def test_quality_flags():
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2023-01-02","2023-01-02","2023-01-03"], utc=True),
        "symbol":["AAA","AAA","AAA"],
        "open":[1,1,2],"high":[2,2,3],"low":[0.5,0.5,1.5],"close":[1.5,1.5,-1.0],"volume":[10,11,12]
    })
    rep = data_quality_report(df)
    assert rep["duplicates"] >= 1
    assert rep["negative_prices"] >= 1
