# src/strategies/registry.py
from __future__ import annotations

import importlib
import inspect
import logging
import pkgutil
import traceback
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Base sınıfları ve (varsa) parametre şemasını güvenli şekilde import et
# -----------------------------------------------------------------------------
try:
    from src.strategies.base_strategy import BaseStrategy as AILearningBase  # AI tabanı
    try:
        # Projede yoksa sorun olmasın diye "Any" olarak ele alacağız
        from src.strategies.base_strategy import StrategyParameters as _StrategyParameters
    except Exception:
        _StrategyParameters = Any  # type: ignore[misc,assignment]
except Exception:
    class AILearningBase:  # type: ignore[no-redef]
        """Fallback: AI base bulunamadı (discovery yine çalışır)."""
        pass
    _StrategyParameters = Any  # type: ignore[misc,assignment]

try:
    from src.strategies.base import Strategy as RuleBasedBase  # Kural tabanı
except Exception:
    class RuleBasedBase:  # type: ignore[no-redef]
        """Fallback: Rule-based base bulunamadı (discovery yine çalışır)."""
        pass

StrategyParameters = _StrategyParameters  # dışarıda tip adı olarak kullanalım


# -----------------------------------------------------------------------------
# Manuel kayıt defteri (dekoratör destekli)
# -----------------------------------------------------------------------------
STRATEGY_REGISTRY: Dict[str, Callable[..., Any]] = {}


def register_strategy(name: str):
    """
    Strateji sınıflarını/Factory fonksiyonlarını registry'e eklemek için dekoratör.
    Modül import edildiğinde tetiklenir.
    """
    def deco(cls_or_fn):
        STRATEGY_REGISTRY[name] = cls_or_fn
        logger.debug("strategy registered: %s -> %s",
                     name, getattr(cls_or_fn, "__name__", str(cls_or_fn)))
        return cls_or_fn
    return deco


def list_strategies() -> List[str]:
    return sorted(STRATEGY_REGISTRY.keys())


def create(name: str, *args, **kwargs):
    factory = STRATEGY_REGISTRY.get(name)
    if not factory:
        raise KeyError(f"Strategy '{name}' not found. Available: {list_strategies()}")
    return factory(*args, **kwargs)


# -----------------------------------------------------------------------------
# Otomatik keşif (plugins/auto_register varsa)
# -----------------------------------------------------------------------------
def _bootstrap_autodiscovery() -> int:
    """
    src.strategies.plugins.auto_register.bootstrap() mevcutsa çağırır.
    Yoksa sessizce 0 döner.
    """
    try:
        from src.strategies.plugins.auto_register import bootstrap as _auto
    except Exception as e:
        logger.debug("auto_register not available: %s", e)
        return 0
    before = len(STRATEGY_REGISTRY)
    gained = _auto()
    logger.info("auto_discovery registered +%d strategies (total=%d)",
                gained, len(STRATEGY_REGISTRY))
    return len(STRATEGY_REGISTRY) - before


# -----------------------------------------------------------------------------
# Statik bağlar (lazy import) – modüller ağırsa bile UI açılabilsin
# Biçim: ("registry_key", "import.path:ClassName")
# -----------------------------------------------------------------------------
_STATIC_BINDINGS: List[Tuple[str, str]] = [
    # --- AI ---
    ("ai_tree_boost",      "src.strategies.ai.tree_boost:TreeBoostStrategy"),
    ("ai_random_forest",   "src.strategies.ai.random_forest:RandomForestStrategy"),
    ("ai_extra_trees",     "src.strategies.ai.extra_trees:ExtraTreesStrategy"),
    ("ai_logistic",        "src.strategies.ai.logistic:LogisticStrategy"),
    ("ai_svm",             "src.strategies.ai.svm:SVMStrategy"),
    ("ai_knn",             "src.strategies.ai.knn:KNNStrategy"),
    ("ai_xgboost",         "src.strategies.ai.xgboost_strict:XGBoostStrictStrategy"),
    ("ai_lightgbm",        "src.strategies.ai.lightgbm:LightGBMStrategy"),
    ("ai_catboost",        "src.strategies.ai.catboost:CatBoostStrategy"),
    ("ai_naive_bayes",     "src.strategies.ai.naive_bayes:NaiveBayesStrategy"),
    ("ai_lstm",            "src.strategies.ai.lstm:LSTMStrategy"),
    ("ai_online_sgd",      "src.strategies.ai.online_sgd:OnlineSGDStrategy"),

    # --- Rule-based ---
    ("rb_ma_crossover",        "src.strategies.rule_based.ma_crossover:MACrossover"),
    ("rb_breakout",            "src.strategies.rule_based.breakout:Breakout"),
    ("rb_rsi_threshold",       "src.strategies.rule_based.rsi_threshold:RSIThreshold"),
    ("rb_macd",                "src.strategies.rule_based.macd_signal:MACDSignal"),
    ("rb_bollinger_reversion", "src.strategies.rule_based.bollinger_reversion:BollingerReversion"),
    ("rb_donchian_breakout",   "src.strategies.rule_based.donchian_breakout:DonchianBreakout"),
    ("rb_stochastic",          "src.strategies.rule_based.stochastic_osc:StochasticOsc"),
    ("rb_adx_trend",           "src.strategies.rule_based.adx_trend:ADXTrend"),
    ("rb_vol_breakout_atr",    "src.strategies.rule_based.vol_breakout_atr:VolatilityBreakoutATR"),
    ("rb_ichimoku",            "src.strategies.rule_based.ichimoku:IchimokuTrend"),

    # --- Hybrid ---
    ("hy_ensemble_voter",     "src.strategies.hybrid.ensemble_voter:EnsembleVoter"),
    ("hy_meta_labeler",       "src.strategies.hybrid.meta_labeler:MetaLabeler"),
    ("hy_regime_switcher",    "src.strategies.hybrid.regime_switcher:RegimeSwitcher"),
    ("hy_weighted_ensemble",  "src.strategies.hybrid.weighted_ensemble:WeightedEnsemble"),
    ("hy_rule_filter_ai",     "src.strategies.hybrid.rule_filter_ai:RuleFilterAI"),
]


def _import_from_path(spec: str) -> Optional[type]:
    """'pkg.mod:ClassName' -> Class obj (yoksa None)."""
    modpath, _, clsname = spec.partition(":")
    if not modpath or not clsname:
        return None
    try:
        module = importlib.import_module(modpath)
        return getattr(module, clsname, None)
    except Exception as e:
        logger.info("static bind skipped: %s (%s)", spec, e)
        return None


def _bootstrap_static_bindings() -> int:
    """Modülleri import edip sınıfı (gerekirse) registry’ye bağlar."""
    added = 0
    for key, spec in _STATIC_BINDINGS:
        if key in STRATEGY_REGISTRY:
            continue
        cls = _import_from_path(spec)
        if cls is None:
            continue
        STRATEGY_REGISTRY.setdefault(key, cls)
        added += 1
    if added:
        logger.info("static bindings registered +%d (total=%d)", added, len(STRATEGY_REGISTRY))
    return added


# -----------------------------------------------------------------------------
# StrategySpec & discovery
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class StrategySpec:
    qualified_name: str
    display_name: str
    family: str
    module: str
    cls: Type
    param_schema: Optional[Type[Any]]  # StrategyParameters varsa o, yoksa Any


def _looks_like_strategy_class(obj: Any) -> bool:
    """
    Hem rule-based hem AI sınıflarını kapsayan seçici.
    - Somut sınıf olmalı
    - Bizim tabanlardan türemeli veya is_strategy=True olmalı
    """
    if not inspect.isclass(obj) or inspect.isabstract(obj):
        return False

    if getattr(obj, "is_strategy", False):
        return True

    if issubclass(obj, (AILearningBase, RuleBasedBase)):
        return True

    # Yedek sezgisel: fit/train + predict/predict_proba kombinasyonu
    has_train = callable(getattr(obj, "fit", None)) or callable(getattr(obj, "train", None))
    has_pred = callable(getattr(obj, "predict", None)) or callable(getattr(obj, "predict_proba", None))
    return has_train and has_pred


def discover_strategies() -> Dict[str, StrategySpec]:
    import src.strategies as root

    results: Dict[str, StrategySpec] = {}
    errors: Dict[str, str] = {}
    skip_contains = (
        ".features", ".strategy_factory", ".registry", ".adapters", ".base", ".hybrid_v1",
        ".ai.logreg_strategy", ".ai.rf_strategy"  # legacy
    )

    candidates: List[str] = []
    # 1) kök paket üzerinden adayları topla
    if hasattr(root, "__path__"):
        for mi in pkgutil.walk_packages(root.__path__, root.__name__ + "."):
            name = mi.name
            if any(s in name for s in skip_contains):
                continue
            candidates.append(name)

    # 2) gerekirse alt paket fallback
    if not candidates:
        for pkg in ("src.strategies.rule_based", "src.strategies.ai", "src.strategies.hybrid"):
            try:
                mod = importlib.import_module(pkg)
                if hasattr(mod, "__path__"):
                    for mi in pkgutil.walk_packages(mod.__path__, pkg + "."):
                        name = mi.name
                        if any(s in name for s in skip_contains):
                            continue
                        candidates.append(name)
            except Exception as e:
                errors[pkg] = f"{type(e).__name__}: {e}"

    # 3) aday modülleri yükle ve sınıf/spec üret
    for name in candidates:
        try:
            m = importlib.import_module(name)
            for _, obj in inspect.getmembers(m, _looks_like_strategy_class):
                qn = f"{obj.__module__}.{obj.__name__}"

                # --- BURASI: family'yi modül yolundan türet ---
                family = getattr(obj, "family", None)
                if not family:
                    mod = obj.__module__
                    if ".ai." in mod:
                        family = "ai"
                    elif ".rule_based." in mod:
                        family = "rule_based"
                    elif ".hybrid." in mod:
                        family = "hybrid"
                    else:
                        family = "conventional"

                spec = StrategySpec(
                    qualified_name=qn,
                    display_name=getattr(obj, "name", getattr(obj, "display_name", obj.__name__)),
                    family=family,  # <-- burada kullanılıyor
                    module=obj.__module__,
                    cls=obj,
                    param_schema=getattr(obj, "ParamSchema", None),
                )
                results[qn] = spec
        except Exception as e:
            errors[name] = f"{type(e).__name__}: {e}\n{traceback.format_exc(limit=1)}"

    discover_strategies.errors = errors  # UI'de göstermek için
    return results



def get_strategy_class(qualified_name: str) -> Type:
    module_name, class_name = qualified_name.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def get_param_schema(qualified_name: str) -> Type[Any]:
    cls = get_strategy_class(qualified_name)
    return getattr(cls, "ParamSchema", StrategyParameters)


# -----------------------------------------------------------------------------
# Dışarıya tek giriş: bootstrap
# -----------------------------------------------------------------------------
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
