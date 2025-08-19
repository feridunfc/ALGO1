\
import logging
import re
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import feedparser  # type: ignore
except Exception:  # pragma: no cover
    feedparser = None

try:
    import tweepy  # type: ignore
except Exception:  # pragma: no cover
    tweepy = None

@dataclass
class NewsItem:
    title: str
    content: str
    url: Optional[str]
    source: str
    timestamp: datetime
    asset: Optional[str] = None
    language: str = "en"

class NewsFeeder:
    def __init__(self, config: Dict):
        self.config = {
            "rss_feeds": [],
            "twitter": None,
            "asset_keywords": {},
            "refresh_interval": 60,
            **config,
        }
        self._callbacks = []
        self._stop_event = threading.Event()
        self._last_fetch: Dict[str, datetime] = {}

        self.twitter_client = None
        if self.config["twitter"] and tweepy is not None:
            try:
                self.twitter_client = tweepy.Client(
                    bearer_token=self.config["twitter"]["bearer_token"],
                    wait_on_rate_limit=True,
                )
            except Exception as e:
                logger.error(f"Twitter client init failed: {e}")
                self.config["twitter"] = None

    def add_callback(self, callback: Callable[[NewsItem], None]):
        self._callbacks.append(callback)

    def start(self):
        threading.Thread(target=self._run_loop, daemon=True, name="NewsFeeder").start()

    def stop(self):
        self._stop_event.set()

    def _run_loop(self):
        logger.info("NewsFeeder loop started")
        while not self._stop_event.is_set():
            start = time.time()
            try:
                for feed_url in self.config["rss_feeds"]:
                    self._process_rss_feed(feed_url)

                if self.twitter_client is not None:
                    self._process_twitter()
            except Exception as e:
                logger.error(f"News loop error: {e}", exc_info=True)

            elapsed = time.time() - start
            sleep_time = max(0.0, self.config["refresh_interval"] - elapsed)
            time.sleep(sleep_time)

    def _process_rss_feed(self, feed_url: str):
        if feedparser is None:
            logger.warning("feedparser not installed; RSS disabled")
            return
        try:
            last_fetch = self._last_fetch.get(feed_url, datetime.utcnow() - timedelta(hours=1))
            feed = feedparser.parse(feed_url)
            for entry in getattr(feed, "entries", []):
                pub_dt = self._parse_date(entry.get("published_parsed") or entry.get("updated_parsed"))
                if pub_dt and pub_dt > last_fetch:
                    asset = self._detect_asset((entry.get("title") or "") + " " + (entry.get("summary") or ""))
                    item = NewsItem(
                        title=entry.get("title") or "",
                        content=entry.get("summary") or "",
                        url=entry.get("link"),
                        source=feed_url,
                        timestamp=pub_dt,
                        asset=asset,
                        language=self._detect_language(entry.get("title") or ""),
                    )
                    self._dispatch_item(item)
            self._last_fetch[feed_url] = datetime.utcnow()
        except Exception as e:
            logger.error(f"RSS process failed for {feed_url}: {e}")

    def _process_twitter(self):
        if self.twitter_client is None:
            return
        try:
            query = self._build_twitter_query()
            tweets = self.twitter_client.search_recent_tweets(
                query=query,
                max_results=25,
                tweet_fields=["created_at", "text", "lang"],
            )
            if tweets and tweets.data:
                for tw in tweets.data:
                    asset = self._detect_asset(tw.text or "")
                    item = NewsItem(
                        title=f"Tweet",
                        content=tw.text or "",
                        url=None,
                        source="Twitter",
                        timestamp=tw.created_at or datetime.utcnow(),
                        asset=asset,
                        language=getattr(tw, "lang", "en") or "en",
                    )
                    self._dispatch_item(item)
        except Exception as e:
            logger.error(f"Twitter fetch failed: {e}")

    def _build_twitter_query(self) -> str:
        tw = self.config.get("twitter") or {}
        users = " OR ".join(f"from:{u}" for u in tw.get("track_users", []))
        hashtags = " OR ".join(f"#{h}" for h in tw.get("track_hashtags", []))
        keywords = " OR ".join(f"\"{k}\"" for k in tw.get("keywords", []))
        qry = " ".join(x for x in [users, hashtags, keywords] if x)
        if not qry:
            qry = "bitcoin OR ethereum"
        return f"({qry}) -is:retweet"

    def _detect_asset(self, text: str) -> Optional[str]:
        text_lower = (text or "").lower()
        for asset, keywords in (self.config.get("asset_keywords") or {}).items():
            for k in keywords:
                if re.search(rf"\b{re.escape(k.lower())}\b", text_lower):
                    return asset
        return None

    def _detect_language(self, text: str) -> str:
        return "en"

    def _parse_date(self, time_struct) -> Optional[datetime]:
        if time_struct:
            try:
                return datetime(*time_struct[:6])
            except Exception:
                return None
        return None

    def _dispatch_item(self, item: NewsItem):
        for cb in self._callbacks:
            try:
                cb(item)
            except Exception as e:
                logger.error(f"Callback failed for {item.title}: {e}")
