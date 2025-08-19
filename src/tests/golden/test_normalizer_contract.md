# Normalizer Contract (Golden)
- Input must be a non-empty pandas DataFrame
- NaN policy must be applied before scaling
- Lookahead guard: all features used for training/prediction must be strictly past (shifted)
- `fit` then `transform` produces same shape index/columns (except rolling window dropna)
- Clipping: if enabled, output is bounded (sigma-based or [0,1] for MinMax)
