
import plotly.graph_objects as go
import pandas as pd

def equity_curve_chart(equity: pd.Series):
    fig = go.Figure()
    if equity is not None and len(equity) > 0:
        fig.add_trace(go.Scatter(x=equity.index, y=equity.values, mode="lines", name="Equity"))
    fig.update_layout(height=320, margin=dict(l=10,r=10,t=30,b=10), title="Equity Curve")
    return fig

def drawdown_chart(equity: pd.Series):
    fig = go.Figure()
    if equity is not None and len(equity) > 0:
        peak = equity.cummax()
        dd = (equity/peak - 1.0)
        fig.add_trace(go.Scatter(x=dd.index, y=dd.values, mode="lines", name="Drawdown"))
    fig.update_layout(height=320, margin=dict(l=10,r=10,t=30,b=10), title="Drawdown")
    return fig
