import optuna
import logging,os,sys
from copy import deepcopy
from typing import Dict, Any
import numpy as np
# Kendi projenizdeki ana pipeline fonksiyonunu ve config sınıfını import edin
# Bu import yollarının projenize uygun olduğundan emin olun!
from pipeline.orchestrator import run_pipeline
from config.config import AppConfig

# --- YENİ VE SAĞLAM PATH KURULUMU ---
try:
    ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
    SRC = os.path.join(ROOT, "src")
    if SRC not in sys.path:
        sys.path.insert(0, SRC)

    from pipeline.orchestrator import run_pipeline
    from config.config import AppConfig
except ImportError as e:
    raise ImportError(f"Optuna runner'da modül yüklenemedi. Hata: {e}")

logger = logging.getLogger(__name__)


def run_tuning(base_config: AppConfig, param_space: Dict[str, Any], n_trials: int = 50):
    """
    Kullanıcı arayüzünden seçilen herhangi bir stratejinin parametrelerini,
    verilen parametre uzayında (param_space) dinamik olarak optimize eder.
    """
    try:
        import optuna
    except ImportError:
        logger.error("Optuna kütüphanesi kurulu değil. Lütfen 'pip install optuna' komutu ile kurun.")
        return {"error": "Optuna kütüphanesi kurulu değil."}

    def objective(trial: optuna.Trial) -> float:
        # Her deneme için konfigürasyonun derin bir kopyasını al
        run_cfg = deepcopy(base_config)

        # --- DİNAMİK KISIM ---
        # Parametre uzayından deneme parametreleri oluştur
        trial_params = {}
        for name, space in param_space.items():
            if space['type'] == 'int':
                trial_params[name] = trial.suggest_int(name, space['low'], space['high'])
            elif space['type'] == 'float':
                trial_params[name] = trial.suggest_float(name, space['low'], space['high'])
            elif space['type'] == 'categorical':
                trial_params[name] = trial.suggest_categorical(name, space['choices'])

        # Mevcut parametrelerin üzerine deneme parametrelerini yaz.
        # Bu sayede hem model_name gibi sabitler korunur, hem de optimize edilenler güncellenir.
        run_cfg.strategy.params.update(trial_params)

        try:
            # run_pipeline fonksiyonu AppConfig nesnesi ile çalışmalıdır
            result = run_pipeline(run_cfg)
            sharpe = result["metrics"].get("sharpe", -1.0)

            # Optuna'nın çökmesini engellemek için geçersiz değerleri kontrol et
            if not np.isfinite(sharpe):
                return -1.0  # Kötü bir skor olarak işaretle

            return sharpe
        except Exception as e:
            logger.error(f"Optuna denemesi sırasında hata oluştu: {e}", exc_info=True)
            return -2.0  # Başarısız denemeleri daha da kötü bir skorla cezalandır

    study = optuna.create_study(direction="maximize")
    try:
        study.optimize(objective, n_trials=n_trials, timeout=600)  # 10 dk zaman aşımı
    except Exception as e:
        logger.error(f"Optuna optimizasyonu genel bir hatayla durdu: {e}")
        return {"error": f"Optimizasyon hatası: {e}"}

    logger.info("Optimizasyon tamamlandı.")
    logger.info(f"En iyi değer (Sharpe): {study.best_value:.4f}")
    logger.info(f"En iyi parametreler: {study.best_params}")

    return {
        "best_params": study.best_params,
        "best_value": study.best_value,
        "trials": study.trials_dataframe().to_dict('records')
    }