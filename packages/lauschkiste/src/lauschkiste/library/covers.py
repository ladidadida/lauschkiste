"""Cover art of songs: embedded pictures (MP3, FLAC, MP4, Ogg) or an image in the song's folder."""

import base64
import hashlib
import logging
import re
import threading
from pathlib import Path
from typing import Optional, Tuple

import mutagen
from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC
from mutagen.mp4 import MP4Cover

logger = logging.getLogger('lauschkiste.library.covers')

FOLDER_IMAGES = ('cover', 'folder', 'front', 'album')
IMAGE_SUFFIXES = ('.jpg', '.jpeg', '.png', '.webp', '.gif')
NO_COVER = 'none'
CACHE_NAME_RE = re.compile(r'^[0-9a-f]{40}\.(jpg|png|webp|gif)$')

_MIME_SUFFIX = {'image/jpeg': 'jpg', 'image/jpg': 'jpg', 'image/png': 'png', 'image/webp': 'webp',
                'image/gif': 'gif'}


def _embedded(path: Path) -> Optional[Tuple[str, bytes]]:
    try:
        audio = mutagen.File(path)
    except Exception:
        return None
    if audio is None:
        return None
    if isinstance(audio, FLAC):
        for picture in audio.pictures:
            return _MIME_SUFFIX.get(picture.mime, 'jpg'), picture.data
    tags = audio.tags
    if tags is None:
        return None
    for value in tags.values() if hasattr(tags, 'values') else []:
        if isinstance(value, APIC) and value.data:
            return _MIME_SUFFIX.get(value.mime, 'jpg'), value.data
    covers = tags.get('covr') if hasattr(tags, 'get') else None
    if covers:
        cover = covers[0]
        suffix = 'png' if getattr(cover, 'imageformat', None) == MP4Cover.FORMAT_PNG else 'jpg'
        return suffix, bytes(cover)
    blocks = tags.get('metadata_block_picture') if hasattr(tags, 'get') else None
    if blocks:
        try:
            picture = Picture(base64.b64decode(blocks[0]))
            return _MIME_SUFFIX.get(picture.mime, 'jpg'), picture.data
        except Exception:
            return None
    return None


def _folder_image(folder: Path) -> Optional[Path]:
    try:
        candidates = {p.name.lower(): p for p in folder.iterdir() if p.is_file()}
    except OSError:
        return None
    for stem in FOLDER_IMAGES:
        for suffix in IMAGE_SUFFIXES:
            found = candidates.get(stem + suffix)
            if found is not None:
                return found
    return None


class CoverCache:
    """Extracts covers into ``cache_dir`` once; names are content-independent hashes of the source."""

    def __init__(self, cache_dir: str):
        self._dir = Path(cache_dir).expanduser()
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    @property
    def directory(self) -> Path:
        return self._dir

    def _key(self, source: Path) -> str:
        try:
            stamp = source.stat().st_mtime
        except OSError:
            stamp = 0
        return hashlib.sha1(f"{source}:{stamp}".encode()).hexdigest()

    def cover_for(self, song: Path) -> Optional[str]:
        """File name in the cache of the song's cover, or None when it has none."""
        key = self._key(song)
        with self._lock:
            existing = next(self._dir.glob(f'{key}.*'), None)
            if existing is not None:
                return None if existing.suffix == f'.{NO_COVER}' else existing.name
            embedded = _embedded(song)
            if embedded is not None:
                suffix, data = embedded
            else:
                image = _folder_image(song.parent)
                if image is None:
                    (self._dir / f'{key}.{NO_COVER}').touch()
                    return None
                suffix = image.suffix.lower().lstrip('.').replace('jpeg', 'jpg')
                data = image.read_bytes()
            name = f'{key}.{suffix}'
            (self._dir / name).write_bytes(data)
            return name

    def path(self, name: str) -> Optional[Path]:
        if not CACHE_NAME_RE.match(name):
            return None
        path = self._dir / name
        return path if path.is_file() else None

    def flush(self) -> None:
        with self._lock:
            for entry in self._dir.iterdir():
                if entry.is_file():
                    entry.unlink()
