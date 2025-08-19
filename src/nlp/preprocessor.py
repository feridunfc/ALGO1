\
import re
from typing import List, Optional

_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_MENTION_RE = re.compile(r"@\w+")
_HASHTAG_RE = re.compile(r"#\w+")
_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "]+",
    flags=re.UNICODE,
)

class TextPreprocessor:
    """Lightweight text preprocessor for financial/news text."""
    def __init__(self, lower: bool = True, strip_urls: bool = True, strip_mentions: bool = True,
                 strip_hashtags: bool = False, strip_emojis: bool = True, keep_hashtag_text: bool = True):
        self.lower = lower
        self.strip_urls = strip_urls
        self.strip_mentions = strip_mentions
        self.strip_hashtags = strip_hashtags
        self.strip_emojis = strip_emojis
        self.keep_hashtag_text = keep_hashtag_text

    def clean(self, text: str) -> str:
        t = text or ""
        if self.strip_urls:
            t = _URL_RE.sub("", t)
        if self.strip_mentions:
            t = _MENTION_RE.sub("", t)
        if self.strip_hashtags:
            t = _HASHTAG_RE.sub("", t)
        elif self.keep_hashtag_text:
            # turn "#BTC" -> "BTC"
            t = re.sub(r"#(\w+)", r"\1", t)
        if self.strip_emojis:
            t = _EMOJI_RE.sub("", t)
        t = re.sub(r"\s+", " ", t).strip()
        if self.lower:
            t = t.lower()
        return t

    def batch_clean(self, texts: List[str]) -> List[str]:
        return [self.clean(t) for t in texts]
