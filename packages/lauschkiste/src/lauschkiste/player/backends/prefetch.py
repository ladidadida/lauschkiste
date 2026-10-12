"""Reads decoded audio of a network stream ahead on its own thread.

A stalled network read blocks only the reading thread; the player keeps playing what is buffered. The reading thread
owns the stream: it closes it when it is done, so stopping never waits for a stalled read.
"""

import threading
from collections import deque
from typing import Callable, Iterable, Optional


def _seconds(frame) -> float:
    return frame.samples / frame.sample_rate


class Prefetch:
    """Iterates over ``source`` (frames with ``samples`` and ``sample_rate``) buffered up to ``seconds`` of audio."""

    def __init__(self, source: Iterable, seconds: float, on_close: Optional[Callable[[], None]] = None,
                 on_item: Optional[Callable[[int], None]] = None):
        self._source = source
        self._limit = seconds
        self._on_close = on_close
        self._on_item = on_item
        self._cond = threading.Condition()
        self._items: deque = deque()
        self._buffered = 0.0
        self._done = False
        self._stopped = False
        self._error: Optional[BaseException] = None
        self._thread = threading.Thread(target=self._produce, name='local_audio.prefetch', daemon=True)

    def start(self) -> 'Prefetch':
        self._thread.start()
        return self

    def stop(self) -> None:
        with self._cond:
            self._stopped = True
            self._cond.notify_all()

    def wait_ready(self, seconds: float, timeout: float, interrupted: Callable[[], bool]) -> None:
        """Wait until ``seconds`` of audio are buffered, the stream ended, ``timeout`` ran out or ``interrupted()``."""
        waited = 0.0
        with self._cond:
            while self._buffered < seconds and not self._done and waited < timeout:
                if interrupted():
                    return
                self._cond.wait(0.1)
                waited += 0.1

    def __iter__(self):
        while True:
            with self._cond:
                while not self._items and not self._done and not self._stopped:
                    self._cond.wait(0.2)
                if self._items:
                    frame = self._items.popleft()
                    self._buffered -= _seconds(frame)
                    self._cond.notify_all()
                elif self._error is not None and not self._stopped:
                    raise self._error
                else:
                    return
            yield frame

    def _produce(self) -> None:
        try:
            for count, frame in enumerate(self._source):
                with self._cond:
                    while self._buffered >= self._limit and not self._stopped:
                        self._cond.wait(0.2)
                    if self._stopped:
                        return
                    self._items.append(frame)
                    self._buffered += _seconds(frame)
                    self._cond.notify_all()
                if self._on_item is not None:
                    self._on_item(count)
        except Exception as error:
            self._error = error
        finally:
            with self._cond:
                self._done = True
                self._cond.notify_all()
            close = getattr(self._source, 'close', None)
            if close is not None:
                try:
                    close()
                except Exception:
                    pass
            if self._on_close is not None:
                try:
                    self._on_close()
                except Exception:
                    pass
