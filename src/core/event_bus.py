from __future__ import annotations
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, List, Any, Optional, Union
import logging

logger = logging.getLogger("core.event_bus")


class EventBusStats:
    def __init__(self):
        self.events_published = 0
        self.events_processed = 0
        self.events_dropped = 0
        self.max_queue_size = 0
        self.subscribers: Dict[str, int] = {}

    def snapshot(self):
        return {
            "events_published": self.events_published,
            "events_processed": self.events_processed,
            "events_dropped": self.events_dropped,
            "max_queue_size": self.max_queue_size,
            "subscribers": dict(self.subscribers),
        }


class EnhancedEventBus:
    """
    Enhanced asyncio-based event bus with sync/async handlers and basic metrics.
    """
    def __init__(self, max_workers: int = 8, max_queue_size: int = 10000, worker_loop_sleep: float = 0.001):
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = {}
        self._async_subscribers: Dict[str, List[Callable[[Any], Any]]] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False
        self._worker_loop_sleep = worker_loop_sleep
        self._stats = EventBusStats()
        self.on_event_processed: Optional[Callable[[Any], None]] = None

    async def start(self):
        if self._running:
            return
        self._running = True
        loop = asyncio.get_running_loop()
        self._worker_task = loop.create_task(self._event_loop())
        logger.info("EnhancedEventBus started")

    async def stop(self, timeout: float = 2.0):
        if not self._running:
            return
        self._running = False
        if self._worker_task:
            try:
                await asyncio.wait_for(self._worker_task, timeout=timeout)
            except asyncio.TimeoutError:
                self._worker_task.cancel()
                logger.warning("EventBus worker cancel due to timeout")
            finally:
                self._worker_task = None
        try:
            self._executor.shutdown(wait=False)
        except Exception:
            pass
        logger.info("EnhancedEventBus stopped")

    async def publish(self, topic: Union[str, Any], event: Any) -> bool:
        key = self._topic_to_key(topic)
        if not hasattr(event, "topic"):
            try:
                setattr(event, "topic", key)
            except Exception:
                pass
        try:
            await self._queue.put((key, event))
            self._stats.events_published += 1
            qsize = self._queue.qsize()
            if qsize > self._stats.max_queue_size:
                self._stats.max_queue_size = qsize
            return True
        except asyncio.QueueFull:
            self._stats.events_dropped += 1
            logger.warning("EventBus queue full, event dropped: %s", key)
            return False

    async def _event_loop(self):
        while self._running:
            try:
                try:
                    key, event = await asyncio.wait_for(self._queue.get(), timeout=self._worker_loop_sleep)
                except asyncio.TimeoutError:
                    await asyncio.sleep(self._worker_loop_sleep)
                    continue

                with self._lock:
                    sync_handlers = list(self._subscribers.get(key, []))
                    async_handlers = list(self._async_subscribers.get(key, []))

                for cb in sync_handlers:
                    try:
                        self._executor.submit(self._safe_execute, cb, event)
                    except Exception:
                        logger.exception("Failed to submit sync handler to executor")

                for async_cb in async_handlers:
                    try:
                        await self._safe_async_execute(async_cb, event)
                    except Exception:
                        logger.exception("Async handler failure for topic %s", key)

                self._stats.events_processed += 1
                if self.on_event_processed:
                    try:
                        self.on_event_processed(event)
                    except Exception:
                        logger.exception("on_event_processed hook failed")

                try:
                    self._queue.task_done()
                except Exception:
                    pass

            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("EventBus main loop exception")
                await asyncio.sleep(0.01)

    def subscribe(self, topic: Union[str, Any], callback: Callable[[Any], Any], is_async: bool = False):
        key = self._topic_to_key(topic)
        with self._lock:
            if is_async:
                self._async_subscribers.setdefault(key, []).append(callback)
            else:
                self._subscribers.setdefault(key, []).append(callback)
            self._stats.subscribers[key] = self._stats.subscribers.get(key, 0) + 1
        logger.debug("Subscribed handler %s to topic %s (async=%s)", getattr(callback, "__qualname__", repr(callback)), key, is_async)

    def unsubscribe(self, topic: Union[str, Any], callback: Callable[[Any], Any], is_async: bool = False):
        key = self._topic_to_key(topic)
        with self._lock:
            if is_async:
                lst = self._async_subscribers.get(key, [])
            else:
                lst = self._subscribers.get(key, [])
            try:
                lst.remove(callback)
                self._stats.subscribers[key] = max(0, self._stats.subscribers.get(key, 1) - 1)
            except ValueError:
                pass

    def get_stats(self) -> Dict[str, Any]:
        s = self._stats.snapshot()
        s["queue_size"] = self._queue.qsize()
        return s

    def _safe_execute(self, callback: Callable, event: Any):
        try:
            callback(event)
        except Exception:
            logger.exception("Sync handler raised exception")

    async def _safe_async_execute(self, callback: Callable, event: Any):
        try:
            await callback(event)
        except Exception:
            logger.exception("Async handler raised exception")

    @staticmethod
    def _topic_to_key(topic: Union[str, Any]) -> str:
        if topic is None:
            return "NONE"
        if isinstance(topic, str):
            return topic
        if hasattr(topic, "value"):
            return str(topic.value)
        return str(topic)
