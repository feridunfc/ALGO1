
class LiquidityRiskAnalyzer:
    def __init__(self, exchange_api):
        self.api = exchange_api

    async def check_liquidity(self, symbol: str, amount: float):
        ob = await self.api.fetch_order_book(symbol)
        mid = (ob['asks'][0][0] + ob['bids'][0][0]) / 2.0
        spread = ob['asks'][0][0] - ob['bids'][0][0]
        slippage = self._estimate_slippage(ob, amount, mid)
        safe_amount = ob['bids'][0][1] * 0.1
        return {'spread_pct': spread / mid, 'slippage_pct': slippage, 'safe_amount': safe_amount}

    def _estimate_slippage(self, ob, amount, mid):
        filled = 0.0
        cost = 0.0
        for price, qty in ob['asks']:
            fill = min(qty, amount - filled)
            cost += fill * (price - mid)
            filled += fill
            if filled >= amount:
                break
        return (cost / amount) if amount > 0 else 0.0
