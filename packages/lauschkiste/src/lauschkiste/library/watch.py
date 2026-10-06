"""Notice changes to the music folder made outside Lauschkiste (Samba, USB stick, scp)."""

import ctypes
import logging
import os
import select
import struct
import sys
import threading
from typing import Callable, Dict, Optional, Tuple

logger = logging.getLogger('lauschkiste.library.watch')

#: Per folder: its own modification time, the sum of its files' sizes, their newest modification time
Snapshot = Dict[str, Tuple[int, int, int]]

IN_MODIFY = 0x2
IN_ATTRIB = 0x4
IN_CLOSE_WRITE = 0x8
IN_MOVED_FROM = 0x40
IN_MOVED_TO = 0x80
IN_CREATE = 0x100
IN_DELETE = 0x200
IN_DELETE_SELF = 0x400
IN_MOVE_SELF = 0x800
IN_Q_OVERFLOW = 0x4000
IN_IGNORED = 0x8000
IN_ONLYDIR = 0x1000000
IN_ISDIR = 0x40000000
IN_NONBLOCK = 0o4000
IN_CLOEXEC = 0o2000000
WATCH_MASK = (IN_MODIFY | IN_ATTRIB | IN_CLOSE_WRITE | IN_MOVED_FROM | IN_MOVED_TO | IN_CREATE | IN_DELETE
              | IN_DELETE_SELF | IN_MOVE_SELF | IN_ONLYDIR)
EVENT = struct.Struct('iIII')


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


class Inotify:
    """Linux inotify on a folder tree: wakes up only when something below it changes."""

    def __init__(self, root: str):
        if not sys.platform.startswith('linux'):
            raise OSError('inotify needs Linux')
        self.root = root
        self._libc = ctypes.CDLL(None, use_errno=True)
        self._fd = self._libc.inotify_init1(IN_NONBLOCK | IN_CLOEXEC)
        if self._fd < 0:
            raise OSError(ctypes.get_errno(), 'inotify_init1 failed')
        self._folders: Dict[int, str] = {}
        try:
            self._add_tree(root)
        except OSError:
            self.close()
            raise

    def _add_tree(self, top: str) -> None:
        for folder, _, _ in os.walk(top):
            wd = self._libc.inotify_add_watch(self._fd, os.fsencode(folder), WATCH_MASK)
            if wd < 0:
                error = ctypes.get_errno()
                if folder == top or error == 28:
                    raise OSError(error, f"Can't watch '{folder}': {os.strerror(error)}")
                continue
            self._folders[wd] = folder

    def wait(self, timeout: float, wake_fd: int) -> bool:
        """True if something changed within ``timeout`` seconds; returns early when ``wake_fd`` is readable."""
        readable, _, _ = select.select([self._fd, wake_fd], [], [], timeout)
        if self._fd not in readable:
            return False
        try:
            data = os.read(self._fd, 64 * 1024)
        except BlockingIOError:
            return False
        offset = 0
        while offset + EVENT.size <= len(data):
            wd, mask, _, length = EVENT.unpack_from(data, offset)
            name = data[offset + EVENT.size:offset + EVENT.size + length].rstrip(b'\0')
            offset += EVENT.size + length
            if mask & IN_IGNORED:
                self._folders.pop(wd, None)
            elif mask & IN_Q_OVERFLOW:
                logger.debug("inotify queue overflowed")
            elif mask & IN_ISDIR and mask & (IN_CREATE | IN_MOVED_TO) and wd in self._folders:
                try:
                    self._add_tree(os.path.join(self._folders[wd], os.fsdecode(name)))
                except OSError as error:
                    logger.warning(f"New folder is not watched: {error}")
        return True

    def close(self) -> None:
        if self._fd >= 0:
            os.close(self._fd)
            self._fd = -1


class FolderWatcher:
    """Calls ``on_change`` once the tree below ``root()`` changed and then stayed unchanged for one
    interval. Uses inotify where available (no work while nothing changes); otherwise, or on file
    systems where it can't be set up, it polls."""

    def __init__(self, root: Callable[[], Optional[str]], on_change: Callable[[], None], interval: float = 5.0):
        self._root = root
        self._on_change = on_change
        self._interval = interval
        self._stop = threading.Event()
        self._wake_read, self._wake_write = os.pipe()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        watch = self._inotify()
        initial = self._current() if watch is None else {}
        self._thread = threading.Thread(target=self._run, args=(watch, initial), name='library.watch', daemon=True)
        self._thread.start()

    def stop(self) -> Optional[threading.Thread]:
        self._stop.set()
        os.write(self._wake_write, b'x')
        return self._thread

    def _current(self) -> Snapshot:
        root = self._root()
        return snapshot(root) if root and os.path.isdir(root) else {}

    def _changed(self) -> None:
        logger.info("Music folder changed; rescanning the library")
        try:
            self._on_change()
        except Exception:
            logger.exception("Rescan after a folder change failed")

    def _inotify(self) -> Optional[Inotify]:
        root = self._root()
        if not root or not os.path.isdir(root):
            return None
        try:
            return Inotify(root)
        except OSError as error:
            logger.info(f"Watching the music folder by polling every {self._interval:g} s ({error})")
            return None

    def _run(self, watch: Optional[Inotify], initial: Snapshot) -> None:
        if watch is None:
            self._poll(initial)
            return
        changed = False
        try:
            while not self._stop.is_set():
                if watch.wait(self._interval, self._wake_read):
                    changed = True
                elif self._root() != watch.root:
                    watch.close()
                    watch = self._inotify()
                    if watch is None:
                        self._poll(self._current())
                        return
                    changed = True
                elif changed:
                    changed = False
                    self._changed()
        finally:
            if watch is not None:
                watch.close()

    def _poll(self, previous: Snapshot) -> None:
        changed = False
        while not self._stop.wait(self._interval):
            current = self._current()
            if current != previous:
                previous = current
                changed = True
            elif changed:
                changed = False
                self._changed()
