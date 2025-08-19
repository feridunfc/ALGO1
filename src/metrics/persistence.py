
import pandas as pd

def persistence_ratio(per_fold_df: pd.DataFrame, metric: str = "sharpe", top_k: int = 3) -> float:
    """Measures how often top performers in early folds stay top in later folds."""
    if per_fold_df.empty or metric not in per_fold_df.columns: return 0.0
    df = per_fold_df.copy()
    half = max(1, len(df)//2)
    early = df.iloc[:half].sort_values(metric, ascending=False).head(top_k).index
    late = df.iloc[half:].sort_values(metric, ascending=False).head(top_k).index
    inter = set(early).intersection(set(late))
    denom = max(1, min(top_k, len(early), len(late)))
    return float(len(inter) / denom)
