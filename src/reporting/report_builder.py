
from __future__ import annotations
from typing import Dict, Any
import os
import pandas as pd
from backtest.metrics import summarize
from backtest.analyzers import drawdown_series

def generate_report(equity: pd.DataFrame, trades: pd.DataFrame, out_dir: str, title: str = "Backtest Report", freq: str = "D") -> Dict[str, Any]:
    os.makedirs(out_dir, exist_ok=True)
    stats = summarize(equity["equity"], trades, freq=freq)
    eq_path = os.path.join(out_dir, "equity.csv"); tr_path = os.path.join(out_dir, "trades.csv")
    equity.to_csv(eq_path, index=False); trades.to_csv(tr_path, index=False)
    dd = drawdown_series(equity["equity"]).reset_index(drop=True)
    dd_df = pd.DataFrame({"t": equity["t"], "drawdown": dd})
    dd_path = os.path.join(out_dir, "drawdown.csv"); dd_df.to_csv(dd_path, index=False)
    md_path = os.path.join(out_dir, "report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n## Summary\n")
        for k,v in stats.items(): f.write(f"- **{k}**: {v}\n")
    return {"stats": stats, "paths": {"equity": eq_path, "trades": tr_path, "drawdown": dd_path, "md": md_path}}
