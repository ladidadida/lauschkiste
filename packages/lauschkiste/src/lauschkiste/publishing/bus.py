# -*- coding: utf-8 -*-
"""Thread-safe in-process pub/sub bus with last-value caching.

Replaces the ZMQ-based Publisher/PublishServer pair (see
documentation/developers/roadmap-core-architecture.md, "Simplify away ZMQ and nginx"): this is a
single-process app, so a plain thread-safe broadcast is enough -- ZMQ solved a distributed-systems
problem (many independent processes, high throughput) that doesn't apply here.

`publish()` can be called from any thread (components run in RFID reader threads, timer threads,
etc.); subscriber callbacks are invoked synchronously on the publishing thread, so they must be
fast and must not block. The FastAPI bridge hands off to its own event loop via
`asyncio.run_coroutine_threadsafe` rather than doing any real work in the callback itself.
"""

import logging
import threading
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger('jb.pub.bus')

# (topic, payload) -> None. payload is None for a revocation.
Callback = Callable[[str, Optional[Any]], None]


class EventBus:
    def __init__(self):
        self._lock = threading.Lock()
        self._cache: Dict[str, Any] = {}
        self._subscribers: set = set()
        # Re-entrancy guard: a subscriber callback failing and logging that failure could, if a
        # log handler routes through this very bus (see misc/loggingext.py's PubStreamHandler),
        # call publish() again from within publish(). Cap it at one level instead of recursing.
        self._local = threading.local()

    def register(self, callback: Callback) -> None:
        with self._lock:
            self._subscribers.add(callback)

    def unregister(self, callback: Callback) -> None:
        with self._lock:
            self._subscribers.discard(callback)

    def publish(self, topic: str, payload: Optional[Any]) -> None:
        """Publish `payload` for `topic`. `payload=None` revokes the topic."""
        with self._lock:
            if payload is None:
                self._cache.pop(topic, None)
            else:
                self._cache[topic] = payload
            subscribers = tuple(self._subscribers)

        depth = getattr(self._local, 'depth', 0)
        self._local.depth = depth + 1
        try:
            for callback in subscribers:
                try:
                    callback(topic, payload)
                except Exception:
                    if depth == 0:
                        logger.error(f"Event subscriber callback failed for topic '{topic}'", exc_info=True)
                    # else: already inside a publish() dispatch on this thread -- drop silently.
        finally:
            self._local.depth = depth

    def resend(self, topic_prefix: str = '') -> None:
        """Re-send all cached topics under `topic_prefix` to every subscriber."""
        with self._lock:
            matching = [(t, v) for t, v in self._cache.items() if t.startswith(topic_prefix)]
        for topic, payload in matching:
            self.publish(topic, payload)

    def cache_snapshot(self) -> Dict[str, Any]:
        """A shallow copy of the full last-value cache, for a client that just subscribed."""
        with self._lock:
            return dict(self._cache)
