# hybrid_2_bert_lgbm.py
# Uses text sentiment as an extra feature for a LightGBM classifier.

import numpy as np
from module_1_transformer_classifier import SentimentClassifier
from module_6_lgbm_trader import LGBMTrader, LGBMTraderConfig

def train_bert_plus_lgbm(numeric_X, labels, texts):
    sent_model = SentimentClassifier(num_labels=3)
    # In a real project, finetune with domain data. Here we skip fit for speed.
    _, probs = sent_model.predict(texts)
    probs = np.array(probs)  # shape (N,3)
    X_aug = np.concatenate([numeric_X, probs], axis=1)
    trader = LGBMTrader(LGBMTraderConfig(n_estimators=200))
    metrics = trader.fit(X_aug, labels)
    return trader, metrics

if __name__ == "__main__":
    from sklearn.datasets import make_classification
    X, y = make_classification(n_samples=300, n_features=10, random_state=1)
    texts = ["bullish news"]*300
    model, metrics = train_bert_plus_lgbm(X, y, texts)
    print("BERT+LGBM metrics:", metrics)
