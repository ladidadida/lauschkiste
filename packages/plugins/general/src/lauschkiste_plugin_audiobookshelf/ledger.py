"""What the box knows about the positions of the books, so that it keeps working without the server."""

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger('lauschkiste.audiobookshelf')

#: Positions that differ by less than this many seconds are the same position
SAME_SEC = 1.0


class Ledger:
    """Per book: ``position`` (seconds into the book), ``finished``, ``pending`` (not yet sent to the server)
    and ``seen`` (what the server had when we last looked), in one JSON file."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()
        self._data: Dict[str, Dict[str, Any]] = {}
        try:
            data = json.loads(path.read_text())
            if isinstance(data, dict):
                self._data = {key: value for key, value in data.items() if isinstance(value, dict)}
        except (OSError, ValueError):
            pass

    def get(self, book: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            entry = self._data.get(book)
            return dict(entry) if entry else None

    def pending(self):
        with self._lock:
            return [book for book, entry in self._data.items() if entry.get('pending')]

    def update(self, book: str, **fields) -> None:
        with self._lock:
            self._data.setdefault(book, {}).update(fields)
            self._write()

    def forget(self, book: str) -> None:
        with self._lock:
            if self._data.pop(book, None) is not None:
                self._write()

    def _write(self) -> None:
        tmp = self.path.with_name(self.path.name + '.tmp')
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_text(json.dumps(self._data))
            os.replace(tmp, self.path)
        except OSError as error:
            logger.warning(f"Could not save the positions to '{self.path}': {error}")


def same(a: float, b: float) -> bool:
    return abs(a - b) < SAME_SEC


def winner(local: Dict[str, Any], remote_position: float, remote_finished: bool) -> Dict[str, Any]:
    """Which position counts after the box played offline (``local``, pending) and the server answers again.

    Only the server's change since the box last looked matters, not the clocks (a Pi can be days off while offline).
    The box's position wins if the server has not moved; otherwise the furthest position wins and a book finished
    anywhere stays finished."""
    seen = local.get('seen') or {}
    moved = ('position' not in seen or not same(float(seen['position']), remote_position)
             or bool(seen.get('finished')) != remote_finished)
    if not moved:
        return {'position': float(local.get('position') or 0), 'finished': bool(local.get('finished'))}
    finished = remote_finished or bool(local.get('finished'))
    return {'position': max(remote_position, float(local.get('position') or 0)), 'finished': finished}
