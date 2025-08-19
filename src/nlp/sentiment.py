\
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

try:
    import torch
    _HAS_TORCH = True
except Exception:
    _HAS_TORCH = False

from transformers import AutoTokenizer, pipeline
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class SentimentResult:
    text: str
    score: float  # [-1, +1]
    confidence: float
    label: str
    timestamp: datetime
    source: str
    asset: Optional[str] = None
    metadata: Optional[Dict] = None

class SentimentAnalyzer:
    MODEL_MAP = {
        "twitter": "finiteautomata/bertweet-base-sentiment-analysis",
        "general": "distilbert-base-uncased-finetuned-sst-2-english",
        "financial": "mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis",
    }

    def __init__(self, model_type: str = "financial", max_workers: int = 4):
        model_name = self.MODEL_MAP.get(model_type, self.MODEL_MAP["financial"])
        device = 0 if _HAS_TORCH and getattr(torch, "cuda", None) and torch.cuda.is_available() else -1
        self.model = pipeline(
            "sentiment-analysis",
            model=model_name,
            tokenizer=AutoTokenizer.from_pretrained(model_name),
            device=device,
        )
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._results_cache = pd.DataFrame(columns=["timestamp", "asset", "score", "confidence", "source"])

    def analyze(self, text: str, source: str = "unknown", asset: Optional[str] = None) -> Optional[SentimentResult]:
        try:
            out = self.model(text)[0]
            res = SentimentResult(
                text=text,
                score=self._normalize_score(out["label"], float(out["score"])),
                confidence=float(out["score"]),
                label=str(out["label"]),
                timestamp=datetime.utcnow(),
                source=source,
                asset=asset,
            )
            self._cache_result(res)
            return res
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return None

    async def analyze_batch_async(self, texts: List[str], sources: List[str], assets: Optional[List[str]] = None) -> List[SentimentResult]:
        if assets is None:
            assets = [None] * len(texts)
        futures = [self.executor.submit(self.analyze, t, s, a) for t, s, a in zip(texts, sources, assets)]
        results = [f.result() for f in futures]
        return [r for r in results if r is not None]

    def get_market_sentiment(self, window: str = "1h", min_confidence: float = 0.7) -> Dict[str, float]:
        if self._results_cache.empty:
            return {}
        df = self._results_cache[self._results_cache["confidence"] >= min_confidence].copy()
        if df.empty:
            return {}
        df = df.set_index("timestamp")
        df["weighted_score"] = df["score"] * df["confidence"]
        if "asset" in df.columns:
            grouped = df.groupby("asset")["weighted_score"].resample(window).mean()
            return grouped.to_dict()
        return {}

    def _normalize_score(self, label: str, score: float) -> float:
        lab = (label or "").lower()
        if "neg" in lab:
            return -score
        if "pos" in lab:
            return score
        return 0.0

    def _cache_result(self, result: SentimentResult):
        new_row = {
            "timestamp": result.timestamp,
            "asset": result.asset,
            "score": result.score,
            "confidence": result.confidence,
            "source": result.source,
        }
        self._results_cache = pd.concat([self._results_cache, pd.DataFrame([new_row])], ignore_index=True)
        if len(self._results_cache) > 10000:
            self._results_cache = self._results_cache.iloc[-5000:]
