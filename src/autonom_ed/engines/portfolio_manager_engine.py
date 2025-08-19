class PortfolioManagerEngine:
    def __init__(self, starting_equity=100000.0):
        self.cash = float(starting_equity)
        self.equity = float(starting_equity)
        self.weight = 0.0  # -1..+1 (gross)
        self.last_price = None

    def set_price(self, price: float):
        self.last_price = float(price)

    def mark_to_market(self, daily_return: float):
        # P&L proportional to weight
        self.equity *= (1.0 + self.weight * daily_return)
        return self.equity

    def set_target_weight(self, w: float):
        self.weight = float(max(-1.0, min(1.0, w)))
