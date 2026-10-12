"""A function called at a fixed interval from a thread of its own."""

import logging
import threading
from typing import Callable

logger = logging.getLogger('lauschkiste.common.periodic')


class PeriodicThread:
    def __init__(self, name: str, interval: float, function: Callable[[], None]):
        self._interval = interval
        self._function = function
        self._closed = threading.Event()
        self.timer_thread = threading.Thread(target=self._run, name=name, daemon=True)

    def start(self) -> None:
        self.timer_thread.start()

    def close(self) -> None:
        self._closed.set()

    def _run(self) -> None:
        while not self._closed.wait(self._interval):
            try:
                self._function()
            except Exception:
                logger.exception(f"'{self.timer_thread.name}' failed")
