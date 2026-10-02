"""SQLite index of the music library: tags and durations read with mutagen.

Songs are keyed by their path relative to the music library root. A scan only re-reads files whose
modification time or size changed.
"""

import logging
import os
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import mutagen

from lauschkiste.library.files import AUDIO_EXTENSIONS

logger = logging.getLogger('lauschkiste.library.index')

SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS songs (
    path TEXT PRIMARY KEY,
    folder TEXT NOT NULL,
    mtime REAL NOT NULL,
    size INTEGER NOT NULL,
    title TEXT,
    artist TEXT,
    album TEXT,
    albumartist TEXT,
    track TEXT,
    disc TEXT,
    duration REAL
);
CREATE INDEX IF NOT EXISTS songs_album ON songs (albumartist, album);
"""

_SONG_COLUMNS = ('path', 'title', 'artist', 'album', 'albumartist', 'track', 'disc', 'duration')


@dataclass
class ScanResult:
    songs: int
    added: int
    updated: int
    removed: int


def _first(tags, *keys) -> Optional[str]:
    for key in keys:
        value = tags.get(key)
        if value:
            value = value[0] if isinstance(value, list) else value
            text = str(value).strip()
            if text:
                return text
    return None


def read_tags(path: Path) -> Dict[str, Any]:
    """Title, artist, album, albumartist, track, disc and duration of an audio file (missing: None)."""
    try:
        audio = mutagen.File(path, easy=True)
    except Exception as error:
        logger.debug(f"Cannot read tags of '{path}': {error}")
        audio = None
    tags = getattr(audio, 'tags', None) or {}
    duration = getattr(getattr(audio, 'info', None), 'length', None)
    return {
        'title': _first(tags, 'title'),
        'artist': _first(tags, 'artist'),
        'album': _first(tags, 'album'),
        'albumartist': _first(tags, 'albumartist', 'album artist'),
        'track': _first(tags, 'tracknumber'),
        'disc': _first(tags, 'discnumber'),
        'duration': float(duration) if duration else None,
    }


def _sort_number(value: Optional[str]) -> int:
    try:
        return int(str(value).split('/')[0])
    except (TypeError, ValueError):
        return 0


def _prefix(folder: str) -> str:
    folder = folder.strip('/')
    return f'{folder}/' if folder else ''


class LibraryIndex:
    def __init__(self, db_path: str, root_provider: Callable[[], Optional[str]]):
        self._root_provider = root_provider
        self._lock = threading.RLock()
        self._scan_lock = threading.Lock()
        Path(db_path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(Path(db_path).expanduser()), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        with self._lock:
            self._db.execute('PRAGMA journal_mode = WAL')
            version = self._db.execute('PRAGMA user_version').fetchone()[0]
            if version != SCHEMA_VERSION:
                self._db.executescript(f'DROP TABLE IF EXISTS songs; {_SCHEMA} PRAGMA user_version = {SCHEMA_VERSION};')

    def close(self) -> None:
        with self._lock:
            self._db.close()

    @property
    def root(self) -> Optional[Path]:
        root = self._root_provider()
        return Path(root).expanduser().resolve() if root else None

    def relative(self, song_url: str) -> Optional[str]:
        """``song_url`` (absolute below the root, or relative to it) as index key, else None."""
        if not song_url or '://' in song_url:
            return None
        root = self.root
        path = Path(song_url)
        if path.is_absolute():
            if root is None:
                return None
            try:
                return path.resolve().relative_to(root).as_posix()
            except ValueError:
                return None
        return Path(os.path.normpath(song_url)).as_posix()

    def absolute(self, relpath: str) -> Optional[Path]:
        root = self.root
        return None if root is None else root / relpath

    # -- scanning -------------------------------------------------------------------------------

    def _audio_files(self, root: Path):
        for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
            dirnames[:] = sorted(d for d in dirnames if not d.startswith('.'))
            for name in filenames:
                if name.startswith('.') or Path(name).suffix.lower() not in AUDIO_EXTENSIONS:
                    continue
                full = Path(dirpath) / name
                try:
                    stat = full.stat()
                except OSError:
                    continue
                yield full.relative_to(root).as_posix(), full, stat

    def scan(self) -> ScanResult:
        """Bring the index in line with the files on disk. Concurrent calls run one after another."""
        with self._scan_lock:
            root = self.root
            with self._lock:
                known = {row['path']: (row['mtime'], row['size'])
                         for row in self._db.execute('SELECT path, mtime, size FROM songs')}
            if root is None or not root.is_dir():
                logger.warning(f"Music library root '{root}' does not exist; index left unchanged")
                return ScanResult(songs=len(known), added=0, updated=0, removed=0)

            seen = set()
            added = updated = 0
            for relpath, full, stat in self._audio_files(root):
                seen.add(relpath)
                previous = known.get(relpath)
                if previous == (stat.st_mtime, stat.st_size):
                    continue
                tags = read_tags(full)
                folder = Path(relpath).parent.as_posix()
                with self._lock:
                    self._db.execute(
                        'INSERT OR REPLACE INTO songs (path, folder, mtime, size, title, artist, album, albumartist,'
                        ' track, disc, duration) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                        (relpath, folder, stat.st_mtime, stat.st_size, tags['title'], tags['artist'], tags['album'],
                         tags['albumartist'], tags['track'], tags['disc'], tags['duration']))
                if previous is None:
                    added += 1
                else:
                    updated += 1
            removed = [path for path in known if path not in seen]
            with self._lock:
                self._db.executemany('DELETE FROM songs WHERE path = ?', [(path,) for path in removed])
                self._db.commit()
                total = self._db.execute('SELECT COUNT(*) FROM songs').fetchone()[0]
            result = ScanResult(songs=total, added=added, updated=updated, removed=len(removed))
            logger.info(f"Library scan: {result}")
            return result

    # -- queries --------------------------------------------------------------------------------

    def _songs(self, where: str = '', params=()) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._db.execute(f"SELECT {', '.join(_SONG_COLUMNS)} FROM songs {where}", params).fetchall()
        songs = [dict(row) for row in rows]
        songs.sort(key=lambda s: (_sort_number(s['disc']), _sort_number(s['track']), s['path'].casefold()))
        return songs

    def albums(self, folder: str = '') -> List[Dict[str, Any]]:
        """Albums below ``folder``, grouped by album artist (falling back to the artist) and album title."""
        prefix = _prefix(folder)
        with self._lock:
            rows = self._db.execute(
                "SELECT COALESCE(albumartist, artist) AS albumartist, album, COUNT(*) AS songs,"
                " MIN(path) AS first_song FROM songs WHERE album IS NOT NULL AND substr(path, 1, ?) = ?"
                " GROUP BY COALESCE(albumartist, artist), album"
                " ORDER BY LOWER(COALESCE(albumartist, artist, '')), LOWER(album)",
                (len(prefix), prefix)).fetchall()
        return [dict(row) for row in rows]

    def album_songs(self, albumartist: Optional[str], album: str, folder: str = '') -> List[Dict[str, Any]]:
        prefix = _prefix(folder)
        if albumartist is None:
            return self._songs('WHERE album = ? AND albumartist IS NULL AND artist IS NULL AND substr(path, 1, ?) = ?',
                               (album, len(prefix), prefix))
        return self._songs('WHERE album = ? AND COALESCE(albumartist, artist) = ? AND substr(path, 1, ?) = ?',
                           (album, albumartist, len(prefix), prefix))

    def songs_below(self, folder: str) -> List[Dict[str, Any]]:
        prefix = _prefix(folder)
        return self._songs('WHERE substr(path, 1, ?) = ?', (len(prefix), prefix))

    def song(self, relpath: str) -> Optional[Dict[str, Any]]:
        songs = self._songs('WHERE path = ?', (relpath,))
        return songs[0] if songs else None

    def search(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        pattern = f"%{query.strip()}%"
        songs = self._songs(
            'WHERE title LIKE ? OR artist LIKE ? OR album LIKE ? OR albumartist LIKE ? OR path LIKE ?',
            (pattern,) * 5)
        return songs[:limit]

    def count(self) -> int:
        with self._lock:
            return self._db.execute('SELECT COUNT(*) FROM songs').fetchone()[0]
