from src.core.strategy_registry import StrategyBase, StrategyRegistry

@StrategyRegistry.register('threshold_signal')
class ThresholdSignalStrategy(StrategyBase):
    name = 'threshold_signal'
    def __init__(self, score_col='score', entry_thr=0.6, exit_thr=0.5, size=1):
        self.score_col = score_col
        self.entry_thr = entry_thr
        self.exit_thr = exit_thr
        self.size = size
        self.position = 0

    def fit(self, X, y=None):
        return self

    def generate_signal(self, timestamp, row):
        score = float(row.get(self.score_col, 0.0))
        price = float(row.get('close', row.get('Close', row.get('adj_close', 0.0))))
        if self.position == 0 and score >= self.entry_thr:
            self.position = 1
            return {'symbol': 'SYMB', 'side': 'buy', 'size': self.size, 'price': price}
        elif self.position == 1 and score < self.exit_thr:
            self.position = 0
            return {'symbol': 'SYMB', 'side': 'sell', 'size': self.size, 'price': price}
        else:
            return {'symbol': 'SYMB', 'side': 'hold', 'size': 0, 'price': price}
