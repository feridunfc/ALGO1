
from __future__ import annotations
import os
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

HTML_TMPL = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Algo-Trade Report</title>
  <style>
    body {font-family: Arial, sans-serif; margin: 20px;}
    .kpi {display:flex; gap:30px; margin: 10px 0 20px 0;}
    .kpi .box {background:#f3f4f6; padding:12px 16px; border-radius:10px;}
    img {max-width: 100%; height:auto; border:1px solid #ddd; border-radius:8px;}
    table {border-collapse: collapse;}
    th, td {border: 1px solid #ddd; padding: 6px 10px;}
    th {background: #fafafa;}
    .muted{color:#666;}
  </style>
</head>
<body>
  <h2>Run Report</h2>
  <div class="kpi">
    <div class="box">Total Return: <b>{total_return:.2%}</b></div>
    <div class="box">Sharpe: <b>{sharpe:.2f}</b></div>
    <div class="box">MaxDD: <b>{maxdd:.2%}</b></div>
  </div>

  <h3>Portfolio Equity</h3>
  <p class="muted">Equity curve for the combined portfolio.</p>
  <img src="equity.png" alt="equity curve"/>

  <h3>Config Summary</h3>
  <table>
    <tr><th>Profile</th><td>{profile}</td></tr>
    <tr><th>Pack</th><td>{pack}</td></tr>
    <tr><th>Strategy</th><td>{strategy}</td></tr>
    <tr><th>Capital</th><td>{capital:,.2f}</td></tr>
    <tr><th>Fees/Slippage (bps)</th><td>{fees_bps}/{slippage_bps}</td></tr>
    <tr><th>Weighting</th><td>{weighting}</td></tr>
  </table>
</body>
</html>
"""

def build_full_html_report(out_dir: str, context: dict) -> str:
    out = Path(out_dir)
    eq_csv = out / "equity.csv"
    if eq_csv.exists():
        df = pd.read_csv(eq_csv, parse_dates=["t"])
        fig = plt.figure(figsize=(9, 4.5))
        plt.plot(df["t"], df["equity"])
        plt.title("Portfolio Equity")
        plt.xlabel("Time"); plt.ylabel("Equity ($)")
        fig.tight_layout()
        fig.savefig(out / "equity.png", dpi=120)
        plt.close(fig)

    metrics = context.get("metrics", {})
    cfg = context.get("cfg", {})
    html = HTML_TMPL.format(
        total_return=metrics.get("total_return", 0.0),
        sharpe=metrics.get("sharpe", 0.0),
        maxdd=metrics.get("maxdd", 0.0),
        profile=cfg.get("profile", "beginner"),
        pack=cfg.get("pack", "conventional"),
        strategy=cfg.get("strategy", "ma_crossover"),
        capital=float(cfg.get("capital", 10000)),
        fees_bps=float(cfg.get("fees_bps", 5.0)),
        slippage_bps=float(cfg.get("slippage_bps", 5.0)),
        weighting=cfg.get("weighting", "equal"),
    )
    out_html = out / "report_full.html"
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    return str(out_html)
