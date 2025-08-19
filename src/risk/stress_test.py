
class StressTester:
    def __init__(self, scenarios: dict):
        self.scenarios = scenarios or {}

    def test_portfolio(self, portfolio: dict) -> dict:
        total = sum(portfolio.values()) or 1.0
        out = {}
        for name, moves in self.scenarios.items():
            loss = 0.0
            for sym, val in portfolio.items():
                move = moves.get(sym, 0.0)
                loss += val * move
            out[name] = {'loss': loss, 'loss_pct': loss / total}
        return out
