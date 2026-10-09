"""The cache core module: items of a source (an audiobook, an episode, ...) downloaded to the box.

A plugin or module that can provide content for download registers a provider at ``cache.providers`` under
its source id. The module fetches what the provider's plan lists, in a process of its own with the lowest
priority, keeps the space limit and shows the state.
"""

import json
import logging
import os
from typing import Dict, List, Optional, Protocol

from pydantic import BaseModel, Field

import lauschkiste.paths
from lauschkiste.cache.manager import DownloadManager
from lauschkiste.cache.store import CacheStore
from lauschkiste.contract import CoreModule, OperationError, action, extension_point, query

logger = logging.getLogger('lauschkiste.cache')

RESERVE_BYTES = 1 << 30
MB = 1 << 20


class CacheFile(BaseModel):
    name: str
    url: str
    #: bytes; 0 when the source does not know (the size is then taken from the download)
    size: int = 0
    duration: Optional[float] = None
    headers: Dict[str, str] = {}


class CachePlan(BaseModel):
    title: str = ''
    version: Optional[str] = None
    files: List[CacheFile]


class CacheProvider(Protocol):
    def plan(self, item: str) -> CachePlan:
        """The files that make up an item, with the headers to fetch them; raises :class:`OperationError`."""

    def version(self, item: str) -> Optional[str]:
        """A value that changes when the server's copy of the item changes (from what is already known; no request)."""

    def removable(self, item: str) -> bool:
        """Whether the item may be removed to make room (for example finished or heard). Never for one in progress."""


class CachedFile(BaseModel):
    path: str
    duration: Optional[float] = None


class CachedItem(BaseModel):
    item: str
    title: str = ''
    files: List[CachedFile]


class DownloadState(BaseModel):
    source: str
    item: str
    state: str
    done: int = 0
    total: int = 0
    error: Optional[str] = None
    update_available: bool = False


class Downloads(BaseModel):
    items: List[DownloadState]
    used_bytes: int
    limit_bytes: int
    free_bytes: int


class CacheSettings(BaseModel):
    limit_gb: float = Field(8, ge=0.1, le=2000, title='Space for downloads (GB)',
                            description='All downloaded books and episodes together; a download that would not fit is refused')
    rate_playing_kbps: int = Field(1000, ge=0, le=100000, title='Download speed while playing (kB/s)',
                                   description='Slower while something plays, so that the playback does not stutter; '
                                               '0 waits until the playback stops')
    remove_old: bool = Field(False, title='Remove old downloads when the space is full',
                             description='Deletes the oldest finished books and heard episodes; items in progress stay')


def _name(value: str, what: str) -> str:
    if not value or '/' in value or value in ('.', '..') or value.startswith('.'):
        raise OperationError(422, f'invalid_{what}', f"Invalid {what} '{value}'")
    return value


class Cache(CoreModule):
    """Downloads items of a source to the box, so that they play without the network."""

    name = 'cache'
    interface_version = '1.0'
    concurrency = 'threadsafe'
    settings = CacheSettings
    providers = extension_point('providers', CacheProvider)

    def __init__(self):
        self._ctx = None
        self._store: Optional[CacheStore] = None
        self._manager: Optional[DownloadManager] = None
        self._playing: Optional[bool] = None

    def start(self, ctx) -> None:
        self._ctx = ctx
        self._store = CacheStore(lauschkiste.paths.resolve('cache'))
        self._manager = DownloadManager(self._store)
        ctx.subscribe('player.status', self._on_status)

    def stop(self):
        self._manager.close()
        return []

    def settings_changed(self, changed):
        self._playing = None
        return True

    # -- speed ------------------------------------------------------------------------------

    def _on_status(self, _topic, status) -> None:
        playing = bool(status) and status.get('state') == 'play'
        if playing == self._playing:
            return
        self._playing = playing
        rate = int(self._ctx.config.get('rate_playing_kbps', default=1000))
        try:
            self._store.set_rate((rate or -1) if playing else 0)
        except OSError as error:
            logger.warning(f"Could not set the download speed: {error}")

    def _limit_bytes(self) -> int:
        return int(float(self._ctx.config.get('limit_gb', default=8)) * (1 << 30))

    def _provider(self, source: str):
        _name(source, 'source')
        if source not in self.providers:
            raise OperationError(404, 'unknown_source', f"Nothing can be downloaded from '{source}'")
        return self.providers.get(source)

    # -- reading ----------------------------------------------------------------------------

    def _update_available(self, source: str, item: str) -> bool:
        meta = self._store.complete(source, item)
        if not meta or meta.get('version') is None or source not in self.providers:
            return False
        try:
            current = self.providers.get(source).version(item)
        except Exception:
            return False
        return current is not None and str(current) != str(meta['version'])

    @query(path='/downloads')
    def downloads(self, source: Optional[str] = None) -> Downloads:
        """Downloaded and downloading items and the space they use."""
        items = [DownloadState(**entry, update_available=self._update_available(entry['source'], entry['item']))
                 for entry in self._manager.states(source)]
        return Downloads(items=items, used_bytes=self._store.used_bytes(), limit_bytes=self._limit_bytes(),
                         free_bytes=self._store.free_bytes())

    def _cached(self, source: str, item: str) -> Optional[CachedItem]:
        meta = self._store.complete(source, item)
        if not meta:
            return None
        directory = self._store.directory(source, item)
        return CachedItem(item=item, title=meta.get('title') or '',
                          files=[CachedFile(path=str(directory / entry['name']), duration=entry.get('duration'))
                                 for entry in meta['files']])

    @query(path='/files')
    def files(self, source: str, item: str) -> Optional[CachedItem]:
        """The files of a complete download (in order), or nothing."""
        return self._cached(_name(source, 'source'), _name(item, 'item'))

    @query(path='/cached')
    def cached(self, source: str) -> List[CachedItem]:
        """All complete downloads of a source."""
        return [entry for entry in (self._cached(*key) for key in self._store.items(_name(source, 'source')))
                if entry is not None]

    # -- changing ---------------------------------------------------------------------------

    def _make_room(self, needed: int) -> None:
        """Remove the oldest removable downloads until ``needed`` bytes fit under the limit."""
        candidates = []
        for source, item in self._store.items():
            if self._store.complete(source, item) and source in self.providers:
                try:
                    removable = self.providers.get(source).removable(item)
                except Exception:
                    removable = False
                if removable:
                    candidates.append((source, item))
        candidates.sort(key=lambda key: (self._store.directory(*key) / 'meta.json').stat().st_mtime)
        for source, item in candidates:
            if self._store.used_bytes() + needed <= self._limit_bytes():
                return
            logger.info(f"Removing the download '{source}/{item}' to make room")
            self._manager.remove(source, item)

    @action()
    def download(self, source: str, item: str) -> None:
        """Download an item so that it plays without the network."""
        provider = self._provider(source)
        _name(item, 'item')
        if self._store.complete(source, item):
            return
        plan = provider.plan(item)
        if not plan.files:
            raise OperationError(422, 'nothing_to_download', 'The item has no files')
        # a source that does not know a size: about 128 kbit/s of audio
        needed = sum(entry.size or int((entry.duration or 1800) * 16000) for entry in plan.files) \
            - self._store.partial_bytes(source, item)
        if self._ctx.config.get('remove_old', default=False):
            self._make_room(needed)
        used, limit, free = self._store.used_bytes(), self._limit_bytes(), self._store.free_bytes()
        if used + needed > limit:
            raise OperationError(409, 'download_cache_full',
                                 f"It needs {needed // MB} MB, {max(0, limit - used) // MB} MB of the "
                                 f"{limit // MB} MB for downloads are free. Remove a download or raise the limit.")
        if free - needed < RESERVE_BYTES:
            raise OperationError(409, 'download_disk_full',
                                 f"It needs {needed // MB} MB, only {free // MB} MB are free on the disk")
        directory = self._store.directory(source, item)
        directory.mkdir(parents=True, exist_ok=True)
        fd = os.open(directory / 'plan.json', os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump(plan.model_dump(mode='json'), stream)
        self._manager.start(source, item)

    @action()
    def cancel(self, source: str, item: str) -> None:
        """Stop a download; what was loaded is kept and continued next time."""
        self._manager.cancel(_name(source, 'source'), _name(item, 'item'))

    @action()
    def remove(self, source: str, item: str) -> None:
        """Delete the downloaded files of an item."""
        self._manager.remove(_name(source, 'source'), _name(item, 'item'))
