"""The download cache of the books and the manager that fills it, one book at a time."""

import json
import logging
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger('lauschkiste.audiobookshelf')

RESERVE_BYTES = 1 << 30


class DownloadCache:
    """``<root>/<book>/``: the audio files, ``meta.json`` once complete, ``status.json`` while downloading."""

    def __init__(self, root: Path):
        self.root = root
        self.rate_file = root / '.rate'

    def directory(self, book: str) -> Path:
        return self.root / book

    def meta(self, book: str) -> Optional[Dict[str, Any]]:
        try:
            meta = json.loads((self.directory(book) / 'meta.json').read_text())
        except (OSError, ValueError):
            return None
        return meta if isinstance(meta, dict) else None

    def complete(self, book: str) -> Optional[Dict[str, Any]]:
        """The metadata of a complete download whose files are all there, else None."""
        meta = self.meta(book)
        if not meta:
            return None
        for entry in meta.get('files', []):
            path = self.directory(book) / entry['name']
            if not path.exists() or path.stat().st_size != entry['size']:
                return None
        return meta

    def status_of(self, book: str) -> Dict[str, Any]:
        try:
            status = json.loads((self.directory(book) / 'status.json').read_text())
        except (OSError, ValueError):
            return {}
        return status if isinstance(status, dict) else {}

    def books(self) -> List[str]:
        try:
            return sorted(entry.name for entry in self.root.iterdir() if entry.is_dir())
        except OSError:
            return []

    def used_bytes(self) -> int:
        total = 0
        for book in self.books():
            for path in self.directory(book).iterdir():
                if path.is_file() and path.name not in ('status.json', 'meta.json'):
                    total += path.stat().st_size
        return total

    def remove(self, book: str) -> None:
        shutil.rmtree(self.directory(book), ignore_errors=True)

    def free_bytes(self) -> int:
        self.root.mkdir(parents=True, exist_ok=True)
        return shutil.disk_usage(self.root).free

    def set_rate(self, kbps: float) -> None:
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            self.rate_file.write_text(str(int(kbps)))
        except OSError as error:
            logger.warning(f"Could not set the download speed: {error}")


class DownloadManager:
    """Runs the downloader process for one book after the other."""

    def __init__(self, cache: DownloadCache, credentials):
        self.cache = cache
        self._credentials = credentials
        self._lock = threading.Condition()
        self._queue: List[str] = []
        self._current: Optional[str] = None
        self._process: Optional[subprocess.Popen] = None
        self._thread: Optional[threading.Thread] = None
        self._closing = False

    # -- control ----------------------------------------------------------------------------

    def start(self, book: str) -> None:
        with self._lock:
            if book == self._current or book in self._queue:
                return
            self._queue.append(book)
            if self._thread is None:
                self._thread = threading.Thread(target=self._run, name='abs-downloads', daemon=True)
                self._thread.start()
            self._lock.notify_all()

    def cancel(self, book: str) -> None:
        with self._lock:
            if book in self._queue:
                self._queue.remove(book)
            if book == self._current and self._process is not None:
                self._process.terminate()

    def remove(self, book: str) -> None:
        self.cancel(book)
        with self._lock:
            while self._current == book:
                self._lock.wait(1.0)
        self.cache.remove(book)

    def close(self) -> None:
        with self._lock:
            self._closing = True
            self._queue.clear()
            if self._process is not None:
                self._process.terminate()
            self._lock.notify_all()

    # -- state ------------------------------------------------------------------------------

    def states(self) -> List[Dict[str, Any]]:
        with self._lock:
            queued, current = list(self._queue), self._current
        result = []
        for book in sorted(set(self.cache.books()) | set(queued) | ({current} if current else set())):
            status = self.cache.status_of(book)
            if self.cache.complete(book):
                state = 'done'
            elif book == current:
                state = status.get('state') or 'downloading'
            elif book in queued:
                state = 'queued'
            elif status.get('state') == 'error':
                state = 'error'
            else:
                state = 'partial'
            result.append({'book': book, 'state': state, 'done': int(status.get('done') or 0),
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
                book = self._queue.pop(0)
                self._current = book
            try:
                self._download(book)
            except Exception:
                logger.exception(f"Download of '{book}' failed")
            finally:
                with self._lock:
                    self._current, self._process = None, None
                    self._lock.notify_all()

    def _download(self, book: str) -> None:
        server, key = self._credentials()
        if not server or not key:
            return
        directory = self.cache.directory(book)
        directory.mkdir(parents=True, exist_ok=True)
        command = [sys.executable, '-m', 'lauschkiste_plugin_audiobookshelf.downloader', server, book,
                   str(directory), str(self.cache.rate_file)]
        process = subprocess.Popen(command, env={**os.environ, 'ABS_API_KEY': key},
                                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        with self._lock:
            self._process = process
        _, errors = process.communicate()
        if process.returncode not in (0, -15) and errors:
            logger.warning(f"Download of '{book}' stopped: {errors.decode(errors='replace').strip()[-300:]}")
