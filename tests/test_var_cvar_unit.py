
import os, sys, pandas as pd, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from risk.var_cvar import historical_var, historical_cvar

def test_var_cvar_monotonic():
    np.random.seed(0)
    r = pd.Series(np.random.normal(0, 0.01, size=1000))
    var90 = historical_var(r, 0.90)
    var95 = historical_var(r, 0.95)
    cvar90 = historical_cvar(r, 0.90)
    cvar95 = historical_cvar(r, 0.95)
    # As alpha increases, tail should be thinner -> VaR smaller (less capital at risk)
    assert var95 <= var90 + 1e-9
    assert cvar95 <= cvar90 + 1e-9
