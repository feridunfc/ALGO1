import streamlit as st
from src.ui.dashboard import show_model_selection, display_errors
from src.ui.compare import show_comparison
from src.data.loader import fetch_yfinance_data
from src.data.normalizer import DataNormalizer
from src.core.strategy_registry import StrategyRegistry
from src.core.backtest import BacktestEngine
from src.core.risk import RiskManager

st.set_page_config(page_title='Algotrade', layout='wide')
tabs = st.tabs(['Data','Models','Run','Compare','Report'])
with tabs[0]:
    st.header('Data Loader')
    sym = st.text_input('Symbol', 'AAPL')
    period = st.selectbox('Period', ['1mo','3mo','6mo','1y','2y','5y'], index=3)
    if st.button('Fetch & Normalize'):
        raw = fetch_yfinance_data(sym, period=period)
        if raw is None:
            st.error('Fetch failed.')
        else:
            df = DataNormalizer.normalize(raw, source='ui')
            if df is None:
                st.error('Normalization failed.')
            else:
                st.session_state['last_df'] = df
                st.success('Data loaded into session.')

with tabs[1]:
    st.header('Models/Strategies')
    show_model_selection()
    st.write('Strategies:', list(StrategyRegistry.list().keys()))

with tabs[2]:
    st.header('Run Backtest')
    if 'last_df' not in st.session_state:
        st.info('Load data first.')
    else:
        df = st.session_state['last_df']
        initial = st.number_input('Initial capital', value=10000.0)
        fees = st.number_input('Fees (bps)', value=0.0)
        slip = st.number_input('Slippage (bps)', value=0.0)
        strat_name = st.selectbox('Strategy', options=list(StrategyRegistry.list().keys()) or ['threshold_signal'])
        if st.button('Run Backtest'):
            strat = StrategyRegistry.get(strat_name)
            engine = BacktestEngine(df, initial_capital=initial, fees_bps=fees/10000.0, slippage_bps=slip/10000.0)
            rm = RiskManager({'max_drawdown':0.5})
            res = engine.run(strat, rm)
            st.session_state['last_results'] = {'run': res}
            st.success('Backtest complete.')

with tabs[3]:
    st.header('Compare')
    results = st.session_state.get('last_results', {})
    show_comparison(results)

with tabs[4]:
    st.header('Report')
    if 'last_results' in st.session_state:
        res = st.session_state['last_results']['run']
        st.write('Final equity:', res.get('final_equity'))
        st.line_chart(res.get('equity_curve'))
        st.write('Transactions sample:', res.get('transactions')[:10])
    else:
        st.info('No results yet.')
