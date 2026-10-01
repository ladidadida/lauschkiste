"""Notice changes to the music folder made outside the jukebox (Samba, USB stick, scp)."""

import logging
import os
import threading
from typing import Callable, Dict, Optional, Tuple

logger = logging.getLogger('jb.library.watch')

#: Per folder: its own modification time, the sum of its files' sizes, their newest modification time
Snapshot = Dict[str, Tuple[int, int, int]]


def snapshot(root: str) -> Snapshot:
    """State of the folder tree below ``root``; growing files count as changes too."""
    result: Snapshot = {}
    pending = [root]
    while pending:
        folder = pending.pop()
        try:
            folder_mtime = os.stat(folder).st_mtime_ns
            size = newest = 0
            with os.scandir(folder) as entries:
                for entry in entries:
                    if entry.is_dir(follow_symlinks=False):
                        pending.append(entry.path)
                    elif entry.is_file(follow_symlinks=False):
                        stat = entry.stat(follow_symlinks=False)
                        size += stat.st_size
                        newest = max(newest, stat.st_mtime_ns)
        except OSError:
            continue
        result[folder] = (folder_mtime, size, newest)
    return result


class FolderWatcher:
    """Calls ``on_change`` once the tree below ``root()`` changed and then stayed unchanged for one
    interval. Polls instead of using inotify, so it works on every file system."""

    def __init__(self, root: Callable[[], Optional[str]], on_change: Callable[[], None], interval: float = 5.0):
        self._root = root
        self._on_change = on_change
        self._interval = interval
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        initial = self._current()
        self._thread = threading.Thread(target=self._run, args=(initial,), name='library.watch', daemon=True)
        self._thread.start()

    def stop(self) -> Optional[threading.Thread]:
        self._stop.set()
        return self._thread

    def _current(self) -> Snapshot:
        root = self._root()
        return snapshot(root) if root and os.path.isdir(root) else {}

    def _run(self, previous: Snapshot) -> None:
        changed = False
        while not self._stop.wait(self._interval):
            current = self._current()
            if current != previous:
                previous = current
                changed = True
            elif changed:
                changed = False
                logger.info("Music folder changed; rescanning the library")
                try:
                    self._on_change()
                except Exception:
                    logger.exception("Rescan after a folder change failed")
