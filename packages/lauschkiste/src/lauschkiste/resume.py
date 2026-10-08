"""Continue items (audiobooks, podcast episodes) where they stopped.

An item is a list of files played in order through the player. While it plays, its position (file
and seconds) is taken from ``player.status`` and kept in a JSON file; it counts as finished once
its last file has played to the end.
"""

import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

import lauschkiste.library
import lauschkiste.statefile as statefile

logger = logging.getLogger('lauschkiste.resume')

FINISHED_MARGIN_SEC = 15.0
ACTIVATION_GRACE_SEC = 2.0


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def relative(file: Optional[str]) -> Optional[str]:
    """``file`` relative to the library if it is an absolute path below it."""
    if not file or not os.path.isabs(file):
        return file
    root = os.path.expanduser(lauschkiste.library.root()).rstrip('/') + '/'
    return file[len(root):] if file.startswith(root) else file


class PositionStore(Protocol):
    """Where the position of one item is kept when not in the tracker's own file (e.g. on a server)."""

    def load(self) -> Dict[str, Any]: ...

    def save(self, entry: Dict[str, Any]) -> None: ...


class ResumeTracker:
    """Positions of the items of one module, keyed by item id."""

    def __init__(self, ctx, path: Path, rewind_sec: float = 10.0, save_interval_sec: float = 10.0):
        self._ctx = ctx
        self._path = path
        self._rewind = rewind_sec
        self._save_interval = save_interval_sec
        self._lock = threading.Lock()
        self._save_lock = threading.Lock()
        self._entries: Dict[str, Dict[str, Any]] = {}
        self._dirty = False
        self._saved_at = 0.0
        self._key: Optional[str] = None
        self._files: List[str] = []
        self._activated_at = 0.0
        self._last: Optional[Dict[str, float]] = None
        self._worker = ctx.executor('resume')
        self._store: Optional[PositionStore] = None
        self._store_entry: Optional[Dict[str, Any]] = None
        self._store_sent: Optional[Dict[str, Any]] = None
        self._store_saved_at = 0.0

    def configure(self, rewind_sec: float) -> None:
        self._rewind = rewind_sec

    def start(self) -> None:
        self._entries = {key: entry for key, entry in statefile.read_json(self._path).items()
                         if isinstance(entry, dict)}
        self._ctx.subscribe('player.status', self._on_status)

    def stop(self) -> None:
        with self._lock:
            store, entry, self._store_entry = self._store, self._store_entry, None
            if entry == self._store_sent:
                entry = None
        if store is not None and entry is not None:
            self._send(store, entry)
        self.save()

    # -- entries --------------------------------------------------------------------------------

    def entries(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return {key: dict(entry) for key, entry in self._entries.items()}

    def set_finished(self, key: str, finished: bool) -> None:
        """Mark an item as finished or forget it; either way it starts from the beginning next time."""
        with self._lock:
            if self._key == key:
                self._release()
            if finished:
                self._entries[key] = {'finished': True}
            else:
                self._entries.pop(key, None)
            self._dirty = True
        self._worker.submit(self.save)

    def save(self) -> None:
        with self._save_lock:
            with self._lock:
                if not self._dirty:
                    return
                data = {key: dict(entry) for key, entry in self._entries.items()}
                self._dirty = False
                self._saved_at = time.monotonic()
            try:
                statefile.write_json(self._path, data)
            except OSError as error:
                logger.error(f"Could not save positions to '{self._path}': {error}")

    # -- playback -------------------------------------------------------------------------------

    def play(self, key: str, files: List[str], resume: bool = True, context: Optional[Dict[str, Any]] = None,
             store: Optional[PositionStore] = None) -> None:
        """Play an item: where it stopped (``resume``), else from the beginning. The item that is
        already playing keeps playing, a paused one continues. With a ``store`` the position is read
        from and reported to it instead of the tracker's file."""
        player = self._ctx.modules.player
        status = player.playerstatus()
        with self._lock:
            if store is None:
                if not resume:
                    self._entries.pop(key, None)
                    self._dirty = True
                entry = dict(self._entries.get(key, {}))
            else:
                entry = {}
            current = resume and self._key == key and relative(status.file) in self._files
        if current and status.state == 'play':
            return
        if current and status.state == 'pause':
            player.play()
            return
        if store is not None and resume:
            entry = store.load()
        start, position = 0, 0.0
        if not entry.get('finished') and entry.get('file') in files:
            start = files.index(entry['file'])
            position = max(0.0, _number(entry.get('elapsed')) - self._rewind)
        player.play_files(files, start, position, True, context)
        with self._lock:
            self._flush_store()
            self._key, self._files, self._last = key, list(files), None
            self._store, self._store_entry, self._store_saved_at = store, None, 0.0
            self._store_sent = None
            self._activated_at = time.monotonic()

    def _flush_store(self) -> None:
        """Report the newest position to the store (in the worker); call with the lock held."""
        if self._store is not None and self._store_entry is not None:
            store, entry = self._store, self._store_entry
            self._store_entry = None
            if entry == self._store_sent:
                return
            self._store_sent = entry
            self._store_saved_at = time.monotonic()
            self._worker.submit(self._send, store, entry)

    @staticmethod
    def _send(store: PositionStore, entry: Dict[str, Any]) -> None:
        try:
            store.save(entry)
        except Exception as error:
            logger.warning(f"Could not report the position: {error}")

    def _release(self) -> None:
        self._flush_store()
        self._key, self._files, self._last, self._store = None, [], None, None

    def _on_status(self, _topic: str, status: Optional[Dict[str, Any]]) -> None:
        if not status:
            return
        file = relative(status.get('file'))
        state = status.get('state')
        with self._lock:
            if self._key is None:
                return
            if file not in self._files:
                save = self._left_item()
            elif state in ('play', 'pause'):
                save = self._playing(file, state, status)
            elif state == 'stop':
                save = self._stopped()
            else:
                save = False
        if save:
            self._worker.submit(self.save)

    def _left_item(self) -> bool:
        """Something else plays now; call with the lock held. True if the file needs saving."""
        if time.monotonic() - self._activated_at < ACTIVATION_GRACE_SEC:
            return False
        self._release()
        return True

    def _playing(self, file: str, state: str, status: Dict[str, Any]) -> bool:
        """Remember the position; call with the lock held. True if the file needs saving."""
        if self._store is not None and not _number(status.get('duration')):
            return False
        elapsed = _number(status.get('elapsed'))
        entry = {'file': file, 'elapsed': elapsed, 'finished': False}
        self._last = {'index': self._files.index(file), 'elapsed': elapsed,
                      'duration': _number(status.get('duration'))}
        if self._store is None:
            self._entries[self._key] = entry
            self._dirty = True
            return state == 'pause' or time.monotonic() - self._saved_at >= self._save_interval
        self._store_entry = entry
        if state == 'pause' or time.monotonic() - self._store_saved_at >= self._save_interval:
            self._flush_store()
        return False

    def _stopped(self) -> bool:
        """Playback stopped; call with the lock held. The item counts as finished after its last file."""
        last = self._last
        if (last and last['index'] == len(self._files) - 1 and last['duration']
                and last['elapsed'] >= last['duration'] - FINISHED_MARGIN_SEC):
            if self._store is None:
                self._entries[self._key] = {'finished': True}
                self._dirty = True
            else:
                self._store_entry = {'finished': True}
            self._release()
        self._flush_store()
        return True
