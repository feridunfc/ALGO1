# src/core/event_bus.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Type, Callable, Dict, List, Any, Set, Optional, Deque, Tuple
from collections import defaultdict, deque
from threading import Lock, Thread
from enum import Enum, auto

import asyncio
import inspect
import logging
import warnings
import time
import pandas as pd


# ------------------------------
# Event temel tipleri
# ------------------------------
class EventType(Enum):
    MARKET_DATA = auto()
    ORDER_EVENT = auto()
    RISK_EVENT = auto()
    SYSTEM_EVENT = auto()


@dataclass
class Event:
    """
    Tüm event'lerin temel sınıfı.
    - timestamp otomatik atanır (UTC aware pandas.Timestamp)
    - metadata key/value sözlüğü taşır
    - event_type default olarak SYSTEM_EVENT (alt sınıflar override eder)
    """
    event_type: EventType = EventType.SYSTEM_EVENT
    timestamp: Optional[pd.Timestamp] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = pd.Timestamp.utcnow().tz_localize("UTC")
        if self.metadata is None:
            self.metadata = {}


# Örnek domain event'leri (isteğe göre genişletin)
@dataclass
class MarketDataEvent(Event):
    symbol: str = ""
    data: Optional[pd.DataFrame] = None
    event_type: EventType = EventType.MARKET_DATA


@dataclass
class OrderEvent(Event):
    order_id: str = ""
    symbol: str = ""
    quantity: float = 0.0
    price: float = 0.0
    event_type: EventType = EventType.ORDER_EVENT


# ------------------------------
# EventBus
# ------------------------------
class EventBus:
    """
    Production-ready EventBus:
      • Thread-safe singleton
      • Priority-based dispatch
      • Sync & async handler desteği
      • Queue + backpressure (rate limit)
      • Metrics export, replay, reset, shutdown
      • Legacy shim: start_worker/worker/stop_worker/is_worker_alive
    """
    _instance: Optional["EventBus"] = None
    _lock = Lock()

    # ---- Singleton ----
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialize()
        return cls._instance

    # ---- İç kurulum ----
    def _initialize(self):
        # Subscriptions: {EventSubclass: [(priority, handler), ...]}
        self._handlers: Dict[Type[Event], List[Tuple[int, Callable]]] = defaultdict(list)
        # Handler çağrı sayaçları
        self._handler_stats: Dict[str, int] = defaultdict(int)
        # Sadece debug için: hangi handler hangi event tiplerine abone
        self._subscription_index: Dict[str, Set[str]] = defaultdict(set)
        # Event log (lightweight)
        self._event_log: List[Dict[str, Any]] = []
        # Event queue (backpressure)
        self._queue: Deque[Event] = deque()
        self._max_queue_size: int = 10_000

        # Çalışma durumu
        self._active: bool = True

        # Logger
        self.logger = logging.getLogger("EventBus")
        if not self.logger.handlers:
            # Kısa, renkli olmayan basic config
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            )

        # Asyncio event loop ve worker thread
        self._loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        self._thread: Thread = Thread(
            target=self._run_loop, daemon=True, name="EventBusLoopThread"
        )
        self._thread.start()

    # ---- Event loop ayağa kaldırma ----
    def _run_loop(self):
        """
        Worker thread entrypoint.
        """
        try:
            asyncio.set_event_loop(self._loop)
            self.logger.info("EventBus loop started")
            self._loop.run_until_complete(self._process_queue())
        except Exception:
            self.logger.exception("EventBus loop crashed")
        finally:
            try:
                # Tüm pending task'leri iptal et
                pending = asyncio.all_tasks(self._loop)
                for t in pending:
                    t.cancel()
                self._loop.stop()
            except Exception:
                pass
            self.logger.info("EventBus loop stopped")

    # ---- Queue tüketici coroutine'i ----
    async def _process_queue(self):
        # Hafif bir hız: boşken küçük bir sleep
        idle_sleep = 0.001
        while self._active:
            try:
                event: Optional[Event] = None
                if self._queue:
                    event = self._queue.popleft()
                if event is None:
                    await asyncio.sleep(idle_sleep)
                    continue
                await self._dispatch(event)
            except asyncio.CancelledError:
                break
            except Exception:
                self.logger.exception("EventBus._process_queue error")
                # Crash etmeden devam et

    # ---- Abonelik ----
    def subscribe(self, event_type: Type[Event], handler: Callable, priority: int = 0):
        """
        Bir handler'ı belirli bir Event alt sınıfına abone eder.
        - handler(event) imzalı olmalı
        - priority küçükse daha önce çalışır
        """
        if not callable(handler):
            raise TypeError("Handler must be callable")
        if not (isinstance(event_type, type) and issubclass(event_type, Event)):
            raise TypeError("Must subscribe to Event subclasses only")

        sig = inspect.signature(handler)
        if len(sig.parameters) != 1:
            raise ValueError("Handler must accept exactly one parameter (event)")

        self._handlers[event_type].append((priority, handler))
        self._handlers[event_type].sort(key=lambda x: x[0])

        self._subscription_index[handler.__qualname__].add(event_type.__name__)
        self.logger.debug(
            "Handler %s subscribed to %s (priority=%s)",
            handler.__qualname__, event_type.__name__, priority
        )

    # ---- Dispatch ----
    async def _dispatch(self, event: Event):
        """
        Event'i uygun handler'lara gönderir.
        Hem sync hem async handler'ları destekler.
        """
        log_entry = {
            "ts": event.timestamp,
            "type": type(event).__name__,
            "repr": repr(event),
            "handled": 0,
        }

        handled_any = False

        # Sadece kendi tipi ve base Event üzerinde handler ara
        candidate_types: List[Type[Event]] = [type(event)]
        if Event in type(event).__mro__:
            # Baz sınıf handler'larını da tetiklemek için base Class'ı da ekleyebiliriz:
            # Örn: self._handlers[Event]
            candidate_types.append(Event)

        for et in candidate_types:
            if et in self._handlers:
                for priority, handler in self._handlers[et]:
                    try:
                        if inspect.iscoroutinefunction(handler):
                            await handler(event)
                        else:
                            handler(event)
                        self._handler_stats[handler.__qualname__] += 1
                        log_entry["handled"] += 1
                        handled_any = True
                    except Exception:
                        self.logger.exception(
                            "Handler %s failed for %s",
                            handler.__qualname__, type(event).__name__
                        )

        if not handled_any:
            self.logger.debug("No handlers for %s", type(event).__name__)
        self._event_log.append(log_entry)

    # ---- Publish ----
    def publish(self, event: Event):
        """
        Event'i kuyruğa ekler. Backpressure aktif.
        """
        if not isinstance(event, Event):
            raise TypeError("Only Event instances can be published")
        if not self._active:
            warnings.warn("EventBus inactive; event discarded")
            return

        if len(self._queue) >= self._max_queue_size:
            self.logger.warning("EventBus queue overflow; dropping event")
            return

        self._queue.append(event)

    # ---- Flush (isteğe bağlı) ----
    def drain(self, timeout: float = 2.0) -> bool:
        """
        Kuyruğu boşalana kadar bekler (best-effort).
        Testlerde yardımcıdır. True => muhtemelen boşalttı.
        """
        start = time.time()
        while len(self._queue) > 0 and (time.time() - start) < timeout:
            time.sleep(0.01)
        return len(self._queue) == 0

    # ---- Metrics ----
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_events": len(self._event_log),
            "queue_size": len(self._queue),
            "handlers_called": dict(self._handler_stats),
            "subscriptions": {k.__name__: len(v) for k, v in self._handlers.items()},
        }

    def export_metrics(self) -> Dict[str, Any]:
        s = self.get_stats()
        return {
            "eventbus_total_events": s["total_events"],
            "eventbus_queue_size": s["queue_size"],
            "eventbus_handler_calls": sum(s["handlers_called"].values()),
        }

    # ---- Replay (basit) ----
    def replay(self, from_idx: int = 0, to_idx: Optional[int] = None):
        """
        Basit replay: log'taki event tiplerini sadece bilgi amaçlı döker.
        (Gelişmiş kullanımda gerçek Event nesneleri persist edilip yeniden publish edilebilir.)
        """
        to_idx = to_idx if to_idx is not None else len(self._event_log)
        for i, log in enumerate(self._event_log[from_idx:to_idx], start=from_idx):
            self.logger.info("Replaying log[%s]: %s", i, log["type"])

    # ---- Reset / Shutdown ----
    def reset(self):
        """
        Tüm state'i sıfırlar ve worker loop'u yeniden ayağa kaldırır.
        """
        self.shutdown()
        # Tamamen yeniden kur
        self._initialize()

    def shutdown(self, timeout: float = 2.0):
        """
        Worker loop'u kapatır; çağrı idempotenttir.
        """
        if not getattr(self, "_active", False):
            return

        self._active = False
        try:
            if getattr(self, "_loop", None) is not None and not self._loop.is_closed():
                # Thread-safe stop
                self._loop.call_soon_threadsafe(self._loop.stop)
        except Exception:
            pass

        if getattr(self, "_thread", None):
            self._thread.join(timeout=timeout)

        try:
            if getattr(self, "_loop", None) is not None and not self._loop.is_closed():
                self._loop.close()
        except Exception:
            pass

        # Tekrar başlatılabilir olsun diye referansları temiz tutalım
        self._thread = None
        self._loop = asyncio.new_event_loop()  # istenirse start_worker yeniden kurabilir

        self.logger.info("EventBus shutdown complete")

    # -----------------------------------------------------------------
    # Legacy / ops yardımcıları (geri uyumluluk için)
    # -----------------------------------------------------------------
    def start_worker(self) -> None:
        """
        Arka plan event-loop thread'ini idempotent olarak başlatır.
        (Eski kodlarda start_worker bekleniyorsa.)
        """
        if getattr(self, "_thread", None) and self._thread.is_alive():
            return
        # Eski shutdown'dan sonra yeniden kur
        if getattr(self, "_loop", None) is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
        self._active = True
        self._thread = Thread(target=self._run_loop, daemon=True, name="EventBusLoopThread")
        self._thread.start()

    def worker(self, block: bool = True) -> None:
        """
        Legacy entrypoint:
          • block=True  -> Event loop'u *bu* thread'de bloklayarak çalıştırır
          • block=False -> Arka plan thread'ini başlatır ve döner
        """
        if block:
            # Zaten arka plan çalışıyorsa, join ederek bloklayabiliriz
            if getattr(self, "_thread", None) and self._thread.is_alive():
                self._thread.join()
                return
            # Yeni bir loop kurup bloklayalım
            self._loop = asyncio.new_event_loop()
            self._active = True
            self._run_loop()
        else:
            self.start_worker()

    def stop_worker(self, timeout: float = 2.0) -> None:
        """Legacy alias -> shutdown."""
        self.shutdown(timeout=timeout)

    def is_worker_alive(self) -> bool:
        """Worker thread canlı mı?"""
        return bool(getattr(self, "_thread", None) and self._thread.is_alive())

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """Event loop referansı (read-only erişim)."""
        return self._loop


# Tekil global örnek (opsiyonel)
event_bus = EventBus()
