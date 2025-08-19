# src/strategies/registry.py
from __future__ import annotations
from typing import Callable, Dict, Any, Optional, List, Tuple
import importlib
import logging

logger = logging.getLogger(__name__)

# --- Ana registry ve yardımcılar ------------------------------------------------
STRATEGY_REGISTRY: Dict[str, Callable[..., Any]] = {}

def register_strategy(name: str):
    """
    Strateji sınıf/factory’lerini kayıt etmek için dekoratör.
    Modül import edilince otomatik tetiklenir.
    """
    def deco(cls_or_fn):
        STRATEGY_REGISTRY[name] = cls_or_fn
        logger.debug("strategy registered: %s -> %s", name, getattr(cls_or_fn, "__name__", str(cls_or_fn)))
        return cls_or_fn
    return deco

def list_strategies() -> List[str]:
    return sorted(STRATEGY_REGISTRY.keys())

def create(name: str, *args, **kwargs):
    factory = STRATEGY_REGISTRY.get(name)
    if not factory:
        raise KeyError(f"Strategy '{name}' not found. Available: {list_strategies()}")
    return factory(*args, **kwargs)

# --- Otomatik keşif (varsa) ----------------------------------------------------
def _bootstrap_autodiscovery() -> int:
    """
    src.strategies.plugins.auto_register.bootstrap() varsa çağırır.
    Yoksa sessizce 0 döner.
    """
    try:
        from src.strategies.plugins.auto_register import bootstrap as _auto
    except Exception as e:
        logger.debug("auto_register not available: %s", e)
        return 0
    before = len(STRATEGY_REGISTRY)
    gained = _auto()
    logger.info("auto_discovery registered +%d strategies (total=%d)", gained, len(STRATEGY_REGISTRY))
    return len(STRATEGY_REGISTRY) - before

# --- Statik modül listesi (ağır import’ı geciktirmek için “lazy”) --------------
# Biçim: ("registry_key", "import.path:ClassName")
_STATIC_BINDINGS: List[Tuple[str, str]] = [
    # --- AI ---
    ("ai_tree_boost",           "src.strategies.ai.tree_boost:TreeBoostStrategy"),
    ("ai_random_forest",        "src.strategies.ai.random_forest:RandomForestStrategy"),
    ("ai_extra_trees",          "src.strategies.ai.extra_trees:ExtraTreesStrategy"),
    ("ai_logistic",             "src.strategies.ai.logistic:LogisticStrategy"),
    ("ai_svm",                  "src.strategies.ai.svm:SVMStrategy"),
    ("ai_knn",                  "src.strategies.ai.knn:KNNStrategy"),
    ("ai_xgboost",              "src.strategies.ai.xgboost_strict:XGBoostStrictStrategy"),
    ("ai_lightgbm",             "src.strategies.ai.lightgbm:LightGBMStrategy"),
    ("ai_catboost",             "src.strategies.ai.catboost:CatBoostStrategy"),
    ("ai_naive_bayes",          "src.strategies.ai.naive_bayes:NaiveBayesStrategy"),
    ("ai_lstm",                 "src.strategies.ai.lstm:LSTMStrategy"),

    # --- Rule-based ---
    ("rb_ma_crossover",         "src.strategies.rule_based.ma_crossover:MACrossover"),
    ("rb_breakout",             "src.strategies.rule_based.breakout:Breakout"),
    ("rb_rsi_threshold",        "src.strategies.rule_based.rsi_threshold:RSIThreshold"),
    ("rb_macd",                 "src.strategies.rule_based.macd_signal:MACDSignal"),
    ("rb_bollinger_reversion",  "src.strategies.rule_based.bollinger_reversion:BollingerReversion"),
    ("rb_donchian_breakout",    "src.strategies.rule_based.donchian_breakout:DonchianBreakout"),
    ("rb_stochastic",           "src.strategies.rule_based.stochastic_osc:StochasticOsc"),
    ("rb_adx_trend",            "src.strategies.rule_based.adx_trend:ADXTrend"),
    ("rb_vol_breakout_atr",     "src.strategies.rule_based.vol_breakout_atr:VolatilityBreakoutATR"),
    ("rb_ichimoku",             "src.strategies.rule_based.ichimoku:IchimokuTrend"),

    # --- Hybrid ---
    ("hy_ensemble_voter",       "src.strategies.hybrid.ensemble_voter:EnsembleVoter"),
    ("hy_meta_labeler",         "src.strategies.hybrid.meta_labeler:MetaLabeler"),
    ("hy_regime_switcher",      "src.strategies.hybrid.regime_switcher:RegimeSwitcher"),
    ("hy_weighted_ensemble",    "src.strategies.hybrid.weighted_ensemble:WeightedEnsemble"),
    ("hy_rule_filter_ai",       "src.strategies.hybrid.rule_filter_ai:RuleFilterAI"),
]

def _import_from_path(spec: str) -> Optional[type]:
    """
    'pkg.mod:ClassName' -> Class obj
    """
    modpath, _, clsname = spec.partition(":")
    if not modpath or not clsname:
        return None
    try:
        module = importlib.import_module(modpath)
        return getattr(module, clsname, None)
    except Exception as e:
        logger.warning("could not import %s (%s)", spec, e)
        return None

def _bootstrap_static_bindings() -> int:
    """
    Modülleri import edip (dekoratör yoksa) sınıfı elle registry’ye bağlar.
    Ağır bağımlılıklar yoksa sessizce atlar.
    """
    added = 0
    for key, spec in _STATIC_BINDINGS:
        if key in STRATEGY_REGISTRY:
            continue
        cls = _import_from_path(spec)
        if cls is None:
            continue
        # Eğer modül içinde @register_strategy kullanılmışsa, import ile zaten eklenmiş olabilir.
        # Yine de garanti için elle kaydediyoruz (idempotent).
        STRATEGY_REGISTRY.setdefault(key, cls)
        added += 1
    if added:
        logger.info("static bindings registered +%d strategies (total=%d)", added, len(STRATEGY_REGISTRY))
    return added

# --- Dışarıya tek giriş: bootstrap --------------------------------------------
def bootstrap(mode: str = "auto", strict: bool = False) -> int:
    """
    mode:
      - "auto": önce auto_register.bootstrap() dener; 0 eklenirse statik fallback’e geçer
      - "static": sadece statik bağlar
      - "both": önce auto, sonra statik
    strict: True ise hiç strateji kayıt edilemezse hata fırlatır.
    """
    before = len(STRATEGY_REGISTRY)
    gained = 0

    if mode in ("auto", "both"):
        gained += _bootstrap_autodiscovery()

    if mode in ("static", "both") or (mode == "auto" and gained == 0):
        gained += _bootstrap_static_bindings()

    total = len(STRATEGY_REGISTRY)
    if strict and total == 0:
        raise RuntimeError("No strategies registered. Check optional deps and paths.")
    logger.debug("bootstrap done: +%d (total=%d)", total - before, total)
    return total - before
