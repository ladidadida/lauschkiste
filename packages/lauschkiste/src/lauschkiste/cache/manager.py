"""Runs the worker process for one item after the other."""

import logging
import subprocess
import sys
import threading
from typing import Any, Dict, List, Optional, Tuple

from lauschkiste.cache.store import CacheStore

logger = logging.getLogger('lauschkiste.cache')

Key = Tuple[str, str]


class DownloadManager:
    def __init__(self, store: CacheStore):
        self.store = store
        self._lock = threading.Condition()
        self._queue: List[Key] = []
        self._current: Optional[Key] = None
        self._process: Optional[subprocess.Popen] = None
        self._thread: Optional[threading.Thread] = None
        self._closing = False

    # -- control ----------------------------------------------------------------------------

    def start(self, source: str, item: str) -> None:
        key = (source, item)
        with self._lock:
            if key == self._current or key in self._queue:
                return
            self._queue.append(key)
            if self._thread is None:
                self._thread = threading.Thread(target=self._run, name='cache-downloads', daemon=True)
                self._thread.start()
            self._lock.notify_all()

    def cancel(self, source: str, item: str) -> None:
        key = (source, item)
        with self._lock:
            if key in self._queue:
                self._queue.remove(key)
            if key == self._current and self._process is not None:
                self._process.terminate()

    def remove(self, source: str, item: str) -> None:
        self.cancel(source, item)
        with self._lock:
            while self._current == (source, item):
                self._lock.wait(1.0)
        self.store.remove(source, item)

    def close(self) -> None:
        with self._lock:
            self._closing = True
            self._queue.clear()
            if self._process is not None:
                self._process.terminate()
            self._lock.notify_all()

    # -- state ------------------------------------------------------------------------------

    def states(self, source: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            queued, current = list(self._queue), self._current
        keys = set(self.store.items(source)) | {key for key in queued if not source or key[0] == source}
        if current and (not source or current[0] == source):
            keys.add(current)
        result = []
        for key in sorted(keys):
            status = self.store.status_of(*key)
            if self.store.complete(*key):
                state = 'done'
            elif key == current:
                state = status.get('state') or 'downloading'
            elif key in queued:
                state = 'queued'
            elif status.get('state') == 'error':
                state = 'error'
            else:
                state = 'partial'
            result.append({'source': key[0], 'item': key[1], 'state': state, 'done': int(status.get('done') or 0),
                           'total': int(status.get('total') or 0), 'error': status.get('error')})
        return result

    # -- the worker -------------------------------------------------------------------------

    def _run(self) -> None:
        while True:
            with self._lock:
                while not self._queue and not self._closing:
                    self._lock.wait()
                if self._closing:
                    return
                key = self._queue.pop(0)
                self._current = key
            try:
                self._download(*key)
            except Exception:
                logger.exception(f"Download of '{key[0]}/{key[1]}' failed")
            finally:
                with self._lock:
                    self._current, self._process = None, None
                    self._lock.notify_all()

    def _download(self, source: str, item: str) -> None:
        directory = self.store.directory(source, item)
        if not (directory / 'plan.json').exists():
            return
        command = [sys.executable, '-m', 'lauschkiste.cache.worker', str(directory), str(self.store.rate_file)]
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.PIPE)
        with self._lock:
            self._process = process
        _, errors = process.communicate()
        if process.returncode not in (0, -15) and errors:
            logger.warning(f"Download of '{source}/{item}' stopped: {errors.decode(errors='replace').strip()[-300:]}")
