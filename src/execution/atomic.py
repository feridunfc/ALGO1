
import asyncio

class AtomicTransaction:
    def __init__(self, exchanges):
        self.exchanges = exchanges

    async def execute(self, pairs):
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(ex.get_quote(pair)) for ex, pair in zip(self.exchanges, pairs)]
        quotes = [t.result() for t in tasks]
        if self._check_arbitrage(quotes):
            return await self._execute_trades(quotes)
        return None

    def _check_arbitrage(self, quotes):
        try:
            return quotes[0]['ask'] < quotes[1]['bid']
        except Exception:
            return False

    async def _execute_trades(self, quotes):
        # placeholder: implement venue-specific atomic commit/cancel logic
        return {'status': 'executed', 'quotes': quotes}
