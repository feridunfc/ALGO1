from __future__ import annotations
import os, io, base64
from typing import Dict, Any
import pandas as pd
import matplotlib.pyplot as plt

def _fig_to_b64(fig):
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

def _trades_summary(per: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    rows=[]
    for sym, obj in per.items():
        t = obj.get("trades")
        if t is None or t.empty: continue
        d = t.copy()
        d["symbol"]=sym
        d["pnl"] = d["equity_after"].values - d["equity_before"].values
        d.reset_index(inplace=True)
        rows.append(d[["timestamp","symbol","side","close","equity_before","equity_after","pnl"]])
    return pd.concat(rows) if rows else pd.DataFrame(columns=["timestamp","symbol","side","close","equity_before","equity_after","pnl"])

def build_report(out_dir: str, cfg, metrics: Dict[str, Any], per: Dict[str, Dict[str, Any]]):
    os.makedirs(out_dir, exist_ok=True)
    peq_path = os.path.join(out_dir, "portfolio_equity.csv")
    e = pd.read_csv(peq_path, index_col=0, parse_dates=True) if os.path.exists(peq_path) else pd.DataFrame()

    figs = {}
    if not e.empty and "equity" in e.columns:
        fig1 = plt.figure(figsize=(10,4)); e["equity"].plot(title="Portfolio Equity"); figs["equity"] = _fig_to_b64(fig1)
        fig2 = plt.figure(figsize=(10,2.5)); (e["equity"]/e["equity"].cummax()-1.0).plot(title="Drawdown"); figs["ddown"] = _fig_to_b64(fig2)

    rows=[]
    for sym, obj in per.items():
        m = obj["metrics"]; rows.append({"symbol": sym, "total_return": m["total_return"], "sharpe": m["sharpe"], "maxdd": m["maxdd"]})
    per_tbl = pd.DataFrame(rows).sort_values("sharpe", ascending=False) if rows else pd.DataFrame(columns=["symbol","total_return","sharpe","maxdd"])

    # Trades export + top/worst charts
    trades = _trades_summary(per)
    trades.to_csv(os.path.join(out_dir, "trades_all.csv"), index=False)
    top_b64 = worst_b64 = ""
    if len(trades):
        top = trades.nlargest(10, "pnl"); worst = trades.nsmallest(10, "pnl")
        f = plt.figure(figsize=(8,3)); plt.bar(top["timestamp"].astype(str), top["pnl"]); plt.xticks(rotation=45, ha="right"); plt.title("Top 10 Trades (PnL)"); top_b64=_fig_to_b64(f)
        f = plt.figure(figsize=(8,3)); plt.bar(worst["timestamp"].astype(str), worst["pnl"]); plt.xticks(rotation=45, ha="right"); plt.title("Worst 10 Trades (PnL)"); worst_b64=_fig_to_b64(f)

    met_html = "<br>".join([f"<b>{k}</b>: {v:,.4f}" for k,v in metrics.items()])

    html = f"""<!doctype html><html><head>
<meta charset="utf-8"><title>Algo Report</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"/>
<style>body{{padding:16px}} h1,h2{{margin-top:18px}} img{{max-width:100%;height:auto}}</style>
</head><body>
  <h1>Run Report</h1>
  <p><b>Mode:</b> {cfg.mode} &nbsp; <b>Profile:</b> {cfg.profile} &nbsp; <b>Family:</b> {cfg.family}
     &nbsp; <b>Strategy:</b> {cfg.strategy.name} &nbsp; <b>Capital:</b> {cfg.fees.capital:,.2f}</p>

  <h2>Portfolio</h2>
  <div class="row"><div class="col-12">
    <p>{met_html}</p>
    {("<img src='"+figs.get("equity","")+"'/>") if "equity" in figs else "<em>No equity chart.</em>"}
    {("<img src='"+figs.get("ddown","")+"'/>") if "ddown" in figs else ""}
  </div></div>

  <h2>Per-Asset Stats</h2>
  {per_tbl.to_html(classes="table table-striped table-sm", float_format=lambda x: f"{x:,.4f}")}

  <h2>Top/Worst Trades</h2>
  {("<img src='"+top_b64+"'/>") if top_b64 else ""}
  {("<img src='"+worst_b64+"'/>") if worst_b64 else ""}

  <h2>Trades (first 200)</h2>
  {trades.head(200).to_html(classes="table table-sm", float_format=lambda x: f"{x:,.4f}", index=False)}
  <p class="mt-4"><a href="trades_all.csv" download>Download full trades CSV</a></p>
</body></html>"""
    with open(os.path.join(out_dir, "report.html"), "w", encoding="utf-8") as f:
        f.write(html)
