from .base import Strategy

# AI (10)
from .ai.tree_boost import TreeBoostStrategy
from .ai.random_forest import RandomForestStrategy
from .ai.extra_trees import ExtraTreesStrategy
from .ai.logistic import LogisticStrategy
from .ai.svm import SVMStrategy
from .ai.knn import KNNStrategy
from .ai.xgboost_strict import XGBoostStrictStrategy
from .ai.lightgbm import LightGBMStrategy
from .ai.catboost import CatBoostStrategy
from .ai.naive_bayes import NaiveBayesStrategy
from .ai.lstm import LSTMStrategy

# Rule-based (10)
from .rule_based.ma_crossover import MACrossover
from .rule_based.breakout import Breakout
from .rule_based.rsi_threshold import RSIThreshold
from .rule_based.macd_signal import MACDSignal
from .rule_based.bollinger_reversion import BollingerReversion
from .rule_based.donchian_breakout import DonchianBreakout
from .rule_based.stochastic_osc import StochasticOsc
from .rule_based.adx_trend import ADXTrend
from .rule_based.vol_breakout_atr import VolatilityBreakoutATR
from .rule_based.ichimoku import IchimokuTrend

# Hybrid (5)
from .hybrid.ensemble_voter import EnsembleVoter
from .hybrid.meta_labeler import MetaLabeler
from .hybrid.regime_switcher import RegimeSwitcher
from .hybrid.weighted_ensemble import WeightedEnsemble
from .hybrid.rule_filter_ai import RuleFilterAI

STRATEGY_REGISTRY = {
    # AI
    "ai_tree_boost": TreeBoostStrategy,
    "ai_random_forest": RandomForestStrategy,
    "ai_extra_trees": ExtraTreesStrategy,
    "ai_logistic": LogisticStrategy,
    "ai_svm": SVMStrategy,
    "ai_knn": KNNStrategy,
    "ai_xgboost": XGBoostStrictStrategy,
    "ai_lightgbm": LightGBMStrategy,
    "ai_catboost": CatBoostStrategy,
    "ai_naive_bayes": NaiveBayesStrategy,
    "ai_lstm": LSTMStrategy,

    # Rule-based
    "rb_ma_crossover": MACrossover,
    "rb_breakout": Breakout,
    "rb_rsi_threshold": RSIThreshold,
    "rb_macd": MACDSignal,
    "rb_bollinger_reversion": BollingerReversion,
    "rb_donchian_breakout": DonchianBreakout,
    "rb_stochastic": StochasticOsc,
    "rb_adx_trend": ADXTrend,
    "rb_vol_breakout_atr": VolatilityBreakoutATR,
    "rb_ichimoku": IchimokuTrend,

    # Hybrid
    "hy_ensemble_voter": EnsembleVoter,
    "hy_meta_labeler": MetaLabeler,
    "hy_regime_switcher": RegimeSwitcher,
    "hy_weighted_ensemble": WeightedEnsemble,
    "hy_rule_filter_ai": RuleFilterAI,
}
