
import os, sys, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from reporting.report_builder import generate_report

def test_report_files_created(tmp_dir='/mnt/data/phase6_report_out'):
    os.makedirs(tmp_dir, exist_ok=True)
    eq = pd.DataFrame({
        "t": pd.date_range("2024-01-01", periods=50, freq="D", tz="UTC"),
        "equity": (1+pd.Series([0.001]*50)).cumprod()*100000.0
    })
    trades = pd.DataFrame({"symbol":[],"side":[],"qty":[],"px":[],"fee":[],"t":[],"pnl":[]})
    res = generate_report(eq, trades, tmp_dir, title="Unit Report", freq="D")
    assert os.path.exists(res["paths"]["md"])
    with open(res["paths"]["md"], "r", encoding="utf-8") as f:
        txt = f.read()
    assert "Summary" in txt and "total_return" in txt
