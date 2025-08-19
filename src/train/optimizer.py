"""Simple optimization utilities: GridSearch, RandomSearch and Walk-Forward Analysis (WFA).
- GridSearch: iterable over param grid, evaluate objective (callable)
- RandomSearch: sample parameter combos
- WFA: roll-forward splits and aggregator
Usage example:
    from src.train.optimizer import GridSearch, RandomSearch, walk_forward_analyze
"""
import itertools, random
import numpy as np
import pandas as pd

def _cartesian_product(param_grid):
    keys = list(param_grid.keys())
    for vals in itertools.product(*[param_grid[k] for k in keys]):
        yield dict(zip(keys, vals))

class GridSearch:
    def __init__(self, param_grid):
        self.param_grid = param_grid
    def run(self, objective_fn, max_evals=None):
        results = []
        for i,params in enumerate(_cartesian_product(self.param_grid)):
            if max_evals and i>=max_evals:
                break
            score = objective_fn(params)
            results.append({'params':params,'score':score})
        return sorted(results, key=lambda x: x['score'], reverse=True)

class RandomSearch:
    def __init__(self, param_space, n_iter=50, seed=None):
        self.param_space = param_space
        self.n_iter = n_iter
        self.rnd = random.Random(seed)
    def _sample(self):
        out = {}
        for k,vals in self.param_space.items():
            out[k] = self.rnd.choice(vals)
        return out
    def run(self, objective_fn):
        results = []
        for _ in range(self.n_iter):
            p = self._sample()
            score = objective_fn(p)
            results.append({'params':p,'score':score})
        return sorted(results, key=lambda x: x['score'], reverse=True)

def walk_forward_analyze(prices, strategy_builder, cfg, n_splits=3, train_window=252, test_window=63, objective='sharpe'):
    """Walk-forward: for each split, train on train_window, tune via strategy_builder(params) or builder that picks params,
       then test on following test_window. strategy_builder(signature)=callable(params)->strategy_fn
       prices: DataFrame or dict; cfg passed to engine. Returns list of test metrics per fold and aggregate.
    """
    # flatten prices to a reference index
    if isinstance(prices, dict):
        # pick first symbol's index
        idx = list(prices.values())[0].index
    else:
        idx = prices.index
    results = []
    start = 0
    for fold in range(n_splits):
        train_start = start
        train_end = train_start + train_window
        test_end = train_end + test_window
        if test_end > len(idx):
            break
        train_idx = idx[train_start:train_end]
        test_idx = idx[train_end:test_end]
        train_prices = {k:v.loc[train_idx] for k,v in (prices.items() if isinstance(prices,dict) else {'':prices}.items())}
        test_prices = {k:v.loc[test_idx] for k,v in (prices.items() if isinstance(prices,dict) else {'':prices}.items())}
        # builder should return a strategy_fn ready for backtest
        strategy_fn = strategy_builder(train_prices, cfg)
        # user must supply an engine function accessible in cfg or as global 'engine'
        engine = cfg.get('engine')
        if engine is None:
            raise ValueError('cfg must include engine callable for WFA')
        train_res = engine(train_prices, strategy_fn, cfg)
        test_res = engine(test_prices, strategy_fn, cfg)
        results.append({'fold':fold,'train':train_res['metrics'],'test':test_res['metrics']})
        start += test_window
    # aggregate
    return results
