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
from typing import Any, Dict, List, Optional

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

    def start(self) -> None:
        self._entries = {key: entry for key, entry in statefile.read_json(self._path).items()
                         if isinstance(entry, dict)}
        self._ctx.subscribe('player.status', self._on_status)

    def stop(self) -> None:
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

    def play(self, key: str, files: List[str], resume: bool = True) -> None:
        """Play an item: where it stopped (``resume``), else from the beginning. The item that is
        already playing keeps playing, a paused one continues."""
        player = self._ctx.modules.player
        status = player.playerstatus()
        with self._lock:
            if not resume:
                self._entries.pop(key, None)
                self._dirty = True
            entry = dict(self._entries.get(key, {}))
            current = resume and self._key == key and relative(status.file) in self._files
        if current and status.state == 'play':
            return
        if current and status.state == 'pause':
            player.play()
            return
        start, position = 0, 0.0
        if not entry.get('finished') and entry.get('file') in files:
            start = files.index(entry['file'])
            position = max(0.0, _number(entry.get('elapsed')) - self._rewind)
        player.play_files(files, start, position, True)
        with self._lock:
            self._key, self._files, self._last = key, list(files), None
            self._activated_at = time.monotonic()

    def _release(self) -> None:
        self._key, self._files, self._last = None, [], None

    def _on_status(self, _topic: str, status: Optional[Dict[str, Any]]) -> None:
        if not status:
            return
        file = relative(status.get('file'))
        state = status.get('state')
        save = False
        with self._lock:
            if self._key is None:
                return
            if file not in self._files:
                if time.monotonic() - self._activated_at >= ACTIVATION_GRACE_SEC:
                    self._release()
                    save = True
            elif state in ('play', 'pause'):
                elapsed = _number(status.get('elapsed'))
                self._entries[self._key] = {'file': file, 'elapsed': elapsed, 'finished': False}
                self._last = {'index': self._files.index(file), 'elapsed': elapsed,
                              'duration': _number(status.get('duration'))}
                self._dirty = True
                save = state == 'pause' or time.monotonic() - self._saved_at >= self._save_interval
            elif state == 'stop':
                last = self._last
                if (last and last['index'] == len(self._files) - 1 and last['duration']
                        and last['elapsed'] >= last['duration'] - FINISHED_MARGIN_SEC):
                    self._entries[self._key] = {'finished': True}
                    self._dirty = True
                    self._release()
                save = True
        if save:
            self._worker.submit(self.save)
