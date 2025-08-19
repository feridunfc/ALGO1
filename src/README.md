
# Event-Driven Upgrade 2.9.9 (hotfix)

This drop-in package adds:
- Data layer: CSV/Parquet/YF loader + validators (OHLC, volume spikes) + corporate action hooks.
- Vectorized backtest + Walk-Forward engine without look-ahead.
- Advanced Risk: volatility targeting, max position weight %, correlation checks.
- Async execution engine with simple TWAP fallback and retries.
- Event-driven services: ExecutionService, PortfolioService, ReportingCollector (bus-agnostic, DI friendly).
- Metrics engine: Sharpe, Sortino, MaxDD, Calmar, Annualized returns, Win-rate.
- Monitoring: PerformanceTracker (latency/throughput/backtest_speed).
- Tests & verification helpers.

## Integrate (minimal steps)
1) Add this folder to your repo (e.g. under `ext/ed_event_2_9_9/`) or install as local package path.
2) Import modules where needed, e.g. WalkforwardRunner in your orchestrator, RiskManagerEngine in risk service.
3) For event-driven wiring, pass your `event_bus` instance to the services' constructors.
4) Replace existing simple backtests with `vectorized_backtest` and/or `WalkforwardRunner`.

See each module header for usage snippets.
