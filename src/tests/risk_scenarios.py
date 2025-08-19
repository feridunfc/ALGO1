
from risk.stress_test import StressTester

def test_flash_crash():
    portfolio = {'BTC': 10000, 'ETH': 5000}
    scenarios = {
        '2010_Flash_Crash': {'BTC': -0.3, 'ETH': -0.4},
        '2020_COVID': {'BTC': -0.5, 'ETH': -0.6}
    }
    tester = StressTester(scenarios)
    results = tester.test_portfolio(portfolio)
    assert results['2020_COVID']['loss_pct'] < 0  # negative (loss)
    assert results['2010_Flash_Crash']['loss'] < 0
