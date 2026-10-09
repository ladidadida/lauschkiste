"""What was taken off the "continue" list: an item stays off until its progress changes."""

import threading
from pathlib import Path
from typing import Any, Dict

import lauschkiste.statefile as statefile


class Dismissed:
    """``key -> marker`` in a JSON file. The marker says how far the item was when it was taken off; an item whose
    marker differs from the saved one (it was played on, a new episode came) is back on the list."""

    def __init__(self, path: Path):
        self._path = path
        self._lock = threading.Lock()
        self._data: Dict[str, Any] = {k: v for k, v in statefile.read_json(path).items()}

    def is_hidden(self, key: str, marker: Any) -> bool:
        with self._lock:
            return key in self._data and self._data[key] == marker

    def hide(self, key: str, marker: Any) -> None:
        with self._lock:
            self._data[key] = marker
            data = dict(self._data)
        statefile.write_json(self._path, data)

    def forget(self, key: str) -> None:
        with self._lock:
            if self._data.pop(key, None) is None:
                return
            data = dict(self._data)
        statefile.write_json(self._path, data)
