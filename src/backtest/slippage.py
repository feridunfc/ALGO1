
import numpy as np

class OrderBookSlippageModel:
    def __init__(self, historical_lob):
        self.lob_data = historical_lob  # dict-like timestamp -> {'bids':[(p,q)..],'asks':[(p,q)..], 'mid':m}

    def simulate_fill(self, timestamp, side: str, amount: float):
        lob = self.lob_data.get(timestamp)
        if lob is None:
            return np.nan
        levels = lob['asks'] if side.lower() == 'buy' else lob['bids']
        filled = 0.0
        total_cost = 0.0
        for price, qty in levels:
            fill = min(qty, amount - filled)
            total_cost += fill * price
            filled += fill
            if filled >= amount:
                break
        return total_cost / filled if filled > 0 else np.nan
