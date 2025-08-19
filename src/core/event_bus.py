
from __future__ import annotations
import asyncio
import inspect
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, DefaultDict, Dict, List, Optional, Tuple, Type, Union
from collections import defaultdict
from weakref import WeakMethod, ReferenceType

logger = logging.getLogger("EventBus")

try:
    from pydantic import BaseModel, ValidationError  # type: ignore
    _HAS_PYDANTIC = True
except Exception:  # pragma: no cover
    _HAS_PYDANTIC = False
    class BaseModel:  # type: ignore
        @classmethod
        def validate(cls, v): return v
    class ValidationError(Exception): pass

try:
    from opentelemetry import trace  # type: ignore
    _tracer = trace.get_tracer("eventbus")
except Exception:  # pragma: no cover
    _tracer = None

@dataclass(frozen=True)
class BaseEvent:
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None
    parent_id: Optional[str] = None

    @property
    def event_type(self) -> str:
        return type(self).__name__

    @property
    def version(self) -> str:
        return "1.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "version": self.version,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "event_id": self.event_id,
            "correlation_id": self.correlation_id,
            "parent_id": self.parent_id,
            "metadata": self.metadata,
        }

class _EventSchema(BaseModel):  # type: ignore
    event_type: str
    source: str
    timestamp: datetime
    event_id: str

HandlerT = Union[Callable[[BaseEvent], Any], Callable[[BaseEvent], Awaitable[Any]]]

from dataclasses import dataclass

@dataclass
class _Subscription:
    handler: HandlerT
    priority: int = 0
    is_async: Optional[bool] = None
    once: bool = False
    filter_fn: Optional[Callable[[BaseEvent], bool]] = None
    weakref: bool = False

    def resolve(self) -> HandlerT:
        if self.weakref and isinstance(self.handler, ReferenceType):
            ref = self.handler()
            if ref is None:
                raise ReferenceError("Handler lost (weakref)")
            return ref  # type: ignore
        return self.handler  # type: ignore

PreMW = Callable[[BaseEvent], Optional[BaseEvent]]
PostMW = Callable[[BaseEvent, List[Tuple[str, Any]]], None]

class DropPolicy:
    BLOCK = "block"
    DROP_OLDEST = "drop_oldest"
    DROP_NEW = "drop_new"

class EventBus:
    def __init__(
        self,
        *,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        max_queue: int = 10000,
        workers: int = 4,
        drop_policy: str = DropPolicy.DROP_NEW,
        sticky_events: bool = True,
        audit_logs: bool = True,
        dlq: Optional[asyncio.Queue] = None,
        validate_schema: bool = False,
        max_retries: int = 0,
        retry_backoff: float = 0.2,
    ):
        self.loop = loop or asyncio.get_event_loop()
        self.queue: asyncio.Queue[BaseEvent] = asyncio.Queue(maxsize=max_queue)
        self.drop_policy = drop_policy
        self.sticky_enabled = sticky_events
        self._sticky: Dict[Type[BaseEvent], BaseEvent] = {}

        self._subs: DefaultDict[Type[BaseEvent], List[_Subscription]] = defaultdict(list)
        self._subs_any: List[_Subscription] = []

        self._workers: List[asyncio.Task] = []
        self._stopped = asyncio.Event()
        self._pre: List[PreMW] = []
        self._post: List[PostMW] = []

        self.audit_logs = audit_logs
        self.dlq = dlq
        self.validate_schema = validate_schema and _HAS_PYDANTIC
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

        self.metrics = {"published":0,"processed":0,"dropped":0,"errors":0,"latency_ms_avg":0.0}

        for i in range(workers):
            self._workers.append(self.loop.create_task(self._worker(i)))

    def add_pre_middleware(self, fn: PreMW): self._pre.append(fn)
    def add_post_middleware(self, fn: PostMW): self._post.append(fn)

    def subscribe(
        self,
        event_cls: Type[BaseEvent],
        handler: HandlerT,
        *,
        priority: int = 0,
        is_async: Optional[bool] = None,
        filter_fn: Optional[Callable[[BaseEvent], bool]] = None,
        once: bool = False,
        weakref: bool = False,
        replay_sticky: bool = True,
    ) -> None:
        if is_async is None:
            is_async = inspect.iscoroutinefunction(handler)
        sub = _Subscription(
            handler=handler if not weakref else WeakMethod(handler) if inspect.ismethod(handler) else handler,
            priority=priority, is_async=is_async, once=once, filter_fn=filter_fn, weakref=weakref
        )
        if event_cls is BaseEvent:
            self._subs_any.append(sub)
            self._subs_any.sort(key=lambda s: -s.priority)
        else:
            self._subs[event_cls].append(sub)
            self._subs[event_cls].sort(key=lambda s: -s.priority)

        if self.sticky_enabled and replay_sticky:
            for etype, ev in self._sticky.items():
                if issubclass(etype, event_cls) or (event_cls is etype):
                    self.loop.create_task(self._dispatch_one(ev, sub))

    def unsubscribe(self, event_cls: Type[BaseEvent], handler: HandlerT) -> None:
        def _rm(lst: List[_Subscription]):
            for s in list(lst):
                try:
                    res = s.resolve()
                except ReferenceError:
                    lst.remove(s); continue
                if res == handler:
                    lst.remove(s)
        if event_cls is BaseEvent: _rm(self._subs_any)
        else: _rm(self._subs[event_cls])

    def publish(self, event: BaseEvent) -> None:
        ev = self._preprocess(event)
        if ev is None: return
        try:
            self.queue.put_nowait(ev)
            self.metrics["published"] += 1
        except asyncio.QueueFull:
            self._handle_full_queue(ev)

    async def post(self, event: BaseEvent) -> None:
        ev = self._preprocess(event)
        if ev is None: return
        try:
            await self.queue.put(ev)
            self.metrics["published"] += 1
        except asyncio.QueueFull:
            self._handle_full_queue(ev)

    def publish_sync(self, event: BaseEvent) -> None:
        ev = self._preprocess(event)
        if ev is None: return
        self.loop.run_until_complete(self._dispatch(ev))

    def _preprocess(self, event: BaseEvent) -> Optional[BaseEvent]:
        ev = event
        if self.validate_schema:
            try:
                _EventSchema.validate(ev.to_dict())
            except Exception as e:
                logger.error("Invalid event schema: %s", e)
                return None
        for mw in self._pre:
            ev = mw(ev)
            if ev is None:
                self.metrics["dropped"] += 1
                return None
        if self.sticky_enabled:
            self._sticky[type(ev)] = ev
        return ev

    def _handle_full_queue(self, ev: BaseEvent):
        self.metrics["dropped"] += 1
        if self.drop_policy == "block":
            self.loop.run_until_complete(self.queue.put(ev))
        elif self.drop_policy == "drop_oldest":
            try:
                self.queue.get_nowait()
                self.loop.run_until_complete(self.queue.put(ev))
            except Exception:
                pass
        else:
            if self.audit_logs: logger.warning("Event dropped (queue full): %s", ev.event_type)

    async def request(self, event: BaseEvent, response_cls: Type[BaseEvent], timeout: float = 3.0) -> BaseEvent:
        fut: asyncio.Future = self.loop.create_future()
        corr = event.correlation_id or event.event_id
        def _resp_handler(resp: BaseEvent):
            if resp.correlation_id == corr and not fut.done():
                fut.set_result(resp)
        self.subscribe(response_cls, _resp_handler, once=True, is_async=False, replay_sticky=False)
        await self.post(event)
        return await asyncio.wait_for(fut, timeout=timeout)

    async def adjust_workers(self, new_count: int):
        while len(self._workers) < new_count:
            self._workers.append(self.loop.create_task(self._worker(len(self._workers))))
        while len(self._workers) > new_count:
            t = self._workers.pop()
            t.cancel()
            try: await t
            except Exception: pass

    async def _worker(self, wid: int):
        while not self._stopped.is_set():
            ev = await self.queue.get()
            start = time.perf_counter()
            try:
                await self._dispatch_with_retry(ev)
            except Exception as e:
                self.metrics["errors"] += 1
                logger.exception("Worker-%d dispatch failed: %s", wid, e)
                if self.dlq is not None:
                    try: self.dlq.put_nowait((ev, str(e)))
                    except Exception: pass
            finally:
                self.queue.task_done()
                elapsed = (time.perf_counter() - start) * 1000.0
                a = 0.05
                self.metrics["latency_ms_avg"] = a * elapsed + (1 - a) * self.metrics["latency_ms_avg"]

    async def _dispatch_with_retry(self, ev: BaseEvent):
        retries = 0
        backoff = self.retry_backoff
        while True:
            try:
                await self._dispatch(ev); return
            except Exception:
                retries += 1
                if retries > self.max_retries: raise
                await asyncio.sleep(backoff); backoff *= 2

    async def _dispatch(self, ev: BaseEvent):
        subs: List[_Subscription] = []
        for cls, lst in self._subs.items():
            if isinstance(ev, cls): subs.extend(lst)
        subs.extend(self._subs_any)

        span_ctx = None
        if _tracer is not None:  # pragma: no cover
            span_ctx = _tracer.start_span(ev.event_type)

        results: List[Tuple[str, Any]] = []
        remove: List[Tuple[Type[BaseEvent], _Subscription]] = []

        for sub in subs:
            try:
                h = sub.resolve()
            except ReferenceError:
                for k, lst in self._subs.items():
                    if sub in lst: lst.remove(sub)
                if sub in self._subs_any: self._subs_any.remove(sub)
                continue

            if sub.filter_fn and not sub.filter_fn(ev):
                continue

            try:
                if sub.is_async: res = await h(ev)  # type: ignore
                else: res = h(ev)  # type: ignore
                results.append((getattr(h, "__name__", str(h)), res))
            except Exception as e:
                self.metrics["errors"] += 1
                logger.exception("Handler error (%s): %s", getattr(h, "__name__", h), e)
                results.append((getattr(h, "__name__", str(h)), e))
                if self.dlq is not None:
                    try: self.dlq.put_nowait((ev, f"handler:{getattr(h,'__name__',h)}:{e}"))
                    except Exception: pass

            if sub.once: remove.append((type(ev), sub))

        for mw in self._post:
            try: mw(ev, results)
            except Exception as e:
                logger.exception("post-middleware error: %s", e)

        for et, sub in remove:
            if sub in self._subs_any: self._subs_any.remove(sub)
            else:
                try: self._subs[et].remove(sub)
                except ValueError: pass

        if span_ctx is not None:  # pragma: no cover
            try: span_ctx.end()
            except Exception: pass

        self.metrics["processed"] += 1

    async def _dispatch_one(self, ev: BaseEvent, sub: _Subscription):
        try: h = sub.resolve()
        except ReferenceError: return
        if sub.filter_fn and not sub.filter_fn(ev): return
        if sub.is_async: await h(ev)  # type: ignore
        else: h(ev)  # type: ignore

    async def shutdown(self, timeout: float = 5.0):
        self._stopped.set()
        try: await asyncio.wait_for(self.queue.join(), timeout=timeout)
        except asyncio.TimeoutError: pass
        for t in self._workers:
            t.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)

event_bus = EventBus()

def tracing_middleware_pre(ev: BaseEvent) -> Optional[BaseEvent]:
    logger.debug("[EVT PUBLISH] %s | src=%s | id=%s", ev.event_type, ev.source, ev.event_id)
    return ev

def audit_middleware_post(ev: BaseEvent, results: List[Tuple[str, Any]]) -> None:
    errs = [r for r in results if isinstance(r[1], Exception)]
    if errs:
        logger.warning("[EVT ERR] %s -> %d error(s)", ev.event_type, len(errs))

event_bus.add_pre_middleware(tracing_middleware_pre)
event_bus.add_post_middleware(audit_middleware_post)
