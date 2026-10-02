"""The audiobooks core module: audiobooks in ``library/audiobooks``, continued where they stopped.

Each folder directly below ``audiobooks`` is one audiobook, its files are the chapters in file name
order. The position is kept per audiobook in ``audiobooks.state_file``. Shuffle and repeat are
switched off while an audiobook plays and restored afterwards.
"""

import json
import logging
import os
import re
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

import lauschkiste.library
import lauschkiste.paths
from lauschkiste.contract import CoreModule, OperationError, action, query

logger = logging.getLogger('lauschkiste.audiobooks')

DEFAULT_STATE_FILE = 'settings/audiobooks.json'
FINISHED_MARGIN_SEC = 15.0
ACTIVATION_GRACE_SEC = 2.0


class Audiobook(BaseModel):
    book: str
    title: str
    chapters: int
    duration: Optional[float] = None
    chapter: int = 0
    elapsed: float = 0.0
    listened: float = 0.0
    finished: bool = False
    cover_url: Optional[str] = None


def _natural_key(path: str):
    return [int(part) if part.isdigit() else part.casefold() for part in re.split(r'(\d+)', path)]


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class Audiobooks(CoreModule):
    """Audiobooks: play, continue, start over, mark as finished."""

    name = 'audiobooks'
    interface_version = '1.0'
    concurrency = 'threadsafe'
    requires = ('library', 'player')

    def __init__(self):
        self._ctx = None
        self._lock = threading.Lock()
        self._save_lock = threading.Lock()
        self._path: Optional[Path] = None
        self._rewind = 10.0
        self._save_interval = 10.0
        self._positions: Dict[str, Dict[str, Any]] = {}
        self._dirty = False
        self._saved_at = 0.0
        self._active: Optional[str] = None
        self._chapters: List[str] = []
        self._activated_at = 0.0
        self._last: Optional[Dict[str, float]] = None
        self._modes: Optional[Dict[str, bool]] = None
        self._worker = None

    # -- lifecycle ------------------------------------------------------------------------------

    def start(self, ctx) -> None:
        self._ctx = ctx
        self._path = lauschkiste.paths.resolve(ctx.config.get('state_file', default=DEFAULT_STATE_FILE))
        self._rewind = float(ctx.config.get('rewind_sec', default=10))
        self._save_interval = float(ctx.config.get('save_interval_sec', default=10))
        self._positions = self._load()
        self._worker = ctx.executor('worker')
        ctx.subscribe('player.status', self._on_status)

    def stop(self):
        self._save()
        return []

    # -- state file -----------------------------------------------------------------------------

    def _load(self) -> Dict[str, Dict[str, Any]]:
        try:
            data = json.loads(self._path.read_text())
        except FileNotFoundError:
            return {}
        except (OSError, ValueError) as error:
            logger.error(f"Could not read audiobook positions from '{self._path}': {error}")
            return {}
        return {book: entry for book, entry in data.items() if isinstance(entry, dict)} if isinstance(data, dict) else {}

    def _save(self) -> None:
        with self._save_lock:
            with self._lock:
                if not self._dirty:
                    return
                content = json.dumps(self._positions, indent=2, sort_keys=True)
                self._dirty = False
                self._saved_at = time.monotonic()
            try:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                fd, tmp = tempfile.mkstemp(dir=self._path.parent, prefix='.audiobooks-')
                with os.fdopen(fd, 'w') as stream:
                    stream.write(content)
                os.replace(tmp, self._path)
            except OSError as error:
                logger.error(f"Could not save audiobook positions to '{self._path}': {error}")

    # -- tracking -------------------------------------------------------------------------------

    def _relative(self, file: Optional[str]) -> Optional[str]:
        if not file or not os.path.isabs(file):
            return file
        root = os.path.expanduser(lauschkiste.library.root()).rstrip('/') + '/'
        return file[len(root):] if file.startswith(root) else file

    def _on_status(self, _topic: str, status: Optional[Dict[str, Any]]) -> None:
        if not status:
            return
        file = self._relative(status.get('file'))
        state = status.get('state')
        save = False
        restore = None
        with self._lock:
            if self._active is None:
                return
            if file not in self._chapters:
                if time.monotonic() - self._activated_at < ACTIVATION_GRACE_SEC:
                    return
                restore = self._deactivate()
            elif state in ('play', 'pause'):
                elapsed = _number(status.get('elapsed'))
                self._positions[self._active] = {'file': file, 'elapsed': elapsed, 'finished': False}
                self._last = {'chapter': self._chapters.index(file), 'elapsed': elapsed,
                              'duration': _number(status.get('duration'))}
                self._dirty = True
                save = state == 'pause' or time.monotonic() - self._saved_at >= self._save_interval
            elif state == 'stop':
                last = self._last
                if (last and last['chapter'] == len(self._chapters) - 1 and last['duration']
                        and last['elapsed'] >= last['duration'] - FINISHED_MARGIN_SEC):
                    self._positions[self._active] = {'finished': True}
                    self._dirty = True
                    restore = self._deactivate()
                save = True
        if restore:
            self._worker.submit(self._restore_modes, restore)
        if save or restore is not None:
            self._worker.submit(self._save)

    def _deactivate(self) -> Dict[str, bool]:
        """Forget the active audiobook (lock held); returns the modes to restore."""
        self._active, self._chapters, self._last = None, [], None
        modes, self._modes = self._modes, None
        return modes or {}

    def _restore_modes(self, modes: Dict[str, bool]) -> None:
        player = self._ctx.modules.player
        try:
            if modes.get('random'):
                player.shuffle('enable')
            if modes.get('repeat'):
                player.repeat('enable_repeat_single' if modes.get('single') else 'enable_repeat')
        except Exception as error:
            logger.warning(f"Could not restore shuffle/repeat: {error}")

    # -- library --------------------------------------------------------------------------------

    def _songs(self, book: Optional[str] = None):
        folder = lauschkiste.paths.AUDIOBOOKS_DIR + (f'/{book}' if book else '')
        return self._ctx.modules.library.list_folder_songs(folder)

    def _chapter_files(self, book: str) -> List[str]:
        if not book or '/' in book or book in ('.', '..'):
            raise OperationError(422, 'invalid_audiobook', f"Invalid audiobook name '{book}'")
        files = sorted((song.file for song in self._songs(book)), key=_natural_key)
        if not files:
            raise OperationError(404, 'unknown_audiobook', f"No audiobook '{book}' in the library")
        return files

    # -- operations -----------------------------------------------------------------------------

    @query(path='/')
    def list_books(self) -> List[Audiobook]:
        """All audiobooks with their progress."""
        books: Dict[str, list] = {}
        prefix = lauschkiste.paths.AUDIOBOOKS_DIR + '/'
        for song in self._songs():
            parts = song.file[len(prefix):].split('/', 1)
            if len(parts) == 2:
                books.setdefault(parts[0], []).append(song)
        with self._lock:
            positions = {book: dict(entry) for book, entry in self._positions.items()}
        result = []
        for book in sorted(books, key=_natural_key):
            songs = sorted(books[book], key=lambda song: _natural_key(song.file))
            files = [song.file for song in songs]
            durations = [song.duration or 0.0 for song in songs]
            total = sum(durations) if all(song.duration for song in songs) else None
            entry = positions.get(book, {})
            finished = bool(entry.get('finished'))
            chapter = files.index(entry['file']) if entry.get('file') in files else 0
            elapsed = _number(entry.get('elapsed')) if entry.get('file') in files else 0.0
            listened = total if finished and total else sum(durations[:chapter]) + elapsed
            try:
                cover_url = self._ctx.modules.library.get_song_cover(files[0]).cover_url
            except Exception:
                cover_url = None
            result.append(Audiobook(book=book, title=songs[0].album or book, chapters=len(files), duration=total,
                                    chapter=chapter, elapsed=elapsed, listened=listened, finished=finished,
                                    cover_url=cover_url))
        return result

    @action()
    def play(self, book: str) -> None:
        """Play an audiobook where it stopped (from the beginning when it is new or finished)."""
        self._start(book, resume=True)

    @action()
    def restart(self, book: str) -> None:
        """Play an audiobook from the beginning."""
        self._start(book, resume=False)

    def _start(self, book: str, resume: bool) -> None:
        files = self._chapter_files(book)
        player = self._ctx.modules.player
        status = player.playerstatus()
        with self._lock:
            if not resume:
                self._positions.pop(book, None)
                self._dirty = True
            entry = dict(self._positions.get(book, {}))
            current = resume and self._active == book and self._relative(status.file) in self._chapters
        if current and status.state == 'play':
            return
        if current and status.state == 'pause':
            player.play()
            return
        start, position = 0, 0.0
        if not entry.get('finished') and entry.get('file') in files:
            start = files.index(entry['file'])
            position = max(0.0, _number(entry.get('elapsed')) - self._rewind)
        with self._lock:
            modes = self._modes if self._active else None
        if modes is None:
            modes = {'random': status.random, 'repeat': status.repeat, 'single': status.single}
            if status.random:
                player.shuffle('disable')
            if status.repeat:
                player.repeat('disable')
        player.play_files(files, start, position)
        with self._lock:
            self._active, self._chapters, self._last = book, files, None
            self._activated_at = time.monotonic()
            self._modes = modes

    @action()
    def set_finished(self, book: str, finished: bool = True) -> None:
        """Mark an audiobook as finished (or not); either way it starts from the beginning next time."""
        self._chapter_files(book)
        with self._lock:
            restore = self._deactivate() if self._active == book else None
            if finished:
                self._positions[book] = {'finished': True}
            else:
                self._positions.pop(book, None)
            self._dirty = True
        if restore:
            self._worker.submit(self._restore_modes, restore)
        self._worker.submit(self._save)
