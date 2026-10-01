"""The library core module: file management, index, metadata, cover art and library sources."""

import asyncio
import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Protocol

from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from starlette.requests import Request

import lauschkiste.paths
import lauschkiste.player
from lauschkiste.contract import CoreModule, OperationError, action, event, extension_point, query
from lauschkiste.library.covers import CoverCache
from lauschkiste.library.files import MAX_UPLOAD_SIZE, LibraryError, MusicLibrary
from lauschkiste.library.index import LibraryIndex
from lauschkiste.library.watch import FolderWatcher

logger = logging.getLogger('lauschkiste.library')

LOCAL_SOURCE = 'local'
COVER_ROUTE = '/api/v1/library/covers'
DEFAULT_INDEX = 'settings/library.sqlite'
DEFAULT_COVER_CACHE = 'cache/covers'


class LibrarySource(Protocol):
    """Further music a player backend or plugin can play (e.g. an mpd database, a streaming service)."""

    def describe(self) -> Dict[str, Any]:
        """``{'id', 'label', 'views': [{'id', 'label', 'kind': 'items'|'folders', 'content_types'}]}``"""

    def list_items(self, content_types: Optional[List[str]]) -> List[Dict[str, Any]]:
        """Items (albums, playlists, ...) with ``albumartist``, ``album``, ``content_type``, ``content_uri``."""

    def list_songs(self, albumartist: str, album: str, content_uri: Optional[str]) -> List[Dict[str, Any]]: ...

    def get_song(self, song_url: str) -> Optional[Dict[str, Any]]: ...

    def cover(self, song_url: str) -> Optional[str]:
        """URL of the song's cover (absolute or relative to the web app), or None."""

    def refresh(self) -> None: ...


class LibraryView(BaseModel):
    id: str
    label: str
    kind: Literal['items', 'folders']
    content_types: List[str] = []


class SourceInfo(BaseModel):
    id: str
    label: str
    views: List[LibraryView]


class LibraryItem(BaseModel):
    provider: str
    content_type: str = 'album'
    albumartist: Optional[str] = None
    album: Optional[str] = None
    content_uri: Optional[str] = None
    cover_url: Optional[str] = None


class Song(BaseModel):
    provider: str
    file: str
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    albumartist: Optional[str] = None
    track: Optional[str] = None
    duration: Optional[float] = None
    cover_url: Optional[str] = None


class CoverArt(BaseModel):
    cover_url: Optional[str] = None


class LibraryEntries(BaseModel):
    entries: List[Dict[str, Any]]


class CreatedFolder(BaseModel):
    path: str


class DeletedEntries(BaseModel):
    deleted: List[str]


class ScanStarted(BaseModel):
    scanning: bool


class LibraryScanned(BaseModel):
    songs: int
    added: int
    updated: int
    removed: int


def _duration(value) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def song_from_source(provider: str, data: Dict[str, Any]) -> Song:
    """A :class:`Song` from a source's song mapping (mpd style keys are understood)."""
    def text(key):
        value = data.get(key)
        if isinstance(value, list):
            value = value[0] if value else None
        return None if value in (None, '') else str(value)

    return Song(provider=provider, file=str(data.get('file') or ''), title=text('title'), artist=text('artist'),
                album=text('album'), albumartist=text('albumartist'), track=text('track'),
                duration=_duration(data.get('duration', data.get('time'))), cover_url=text('cover_url'))


class Library(CoreModule):
    """Music library: files, index with metadata, cover art; further sources plug in at ``library.sources``."""

    name = 'library'
    interface_version = '1.0'
    concurrency = 'threadsafe'

    scanned = event('scanned', LibraryScanned)
    sources = extension_point('sources', LibrarySource)

    def __init__(self):
        self._ctx = None
        self._index: Optional[LibraryIndex] = None
        self._covers: Optional[CoverCache] = None
        self._files: Optional[MusicLibrary] = None
        self._scan_pending = threading.Event()
        self._executor = None
        self._file_executor = None
        self._watcher: Optional[FolderWatcher] = None
        self._root_provider = None

    # -- lifecycle ------------------------------------------------------------------------------

    def start(self, ctx) -> None:
        self._ctx = ctx
        path = ctx.config.get('path', default=None)
        root_provider = (lambda: str(lauschkiste.paths.resolve(path))) if path else lauschkiste.player.get_music_library_path
        self._index = LibraryIndex(str(lauschkiste.paths.resolve(ctx.config.get('index', default=DEFAULT_INDEX))),
                                   root_provider)
        self._covers = CoverCache(str(lauschkiste.paths.resolve(ctx.config.get('cover_cache',
                                                                                  default=DEFAULT_COVER_CACHE))))
        self._files = MusicLibrary(root_provider, self._refresh_all)
        self._root_provider = root_provider
        root = root_provider()
        if root:
            Path(root).expanduser().mkdir(parents=True, exist_ok=True)
        self._executor = ctx.executor('scan')
        self._file_executor = ctx.executor('files')

    def ready(self) -> None:
        if self._ctx.config.get('scan_on_startup', default=True):
            self._schedule_scan()
        if self._ctx.config.get('watch', default=True):
            self._watcher = FolderWatcher(self._root_provider, self._schedule_scan,
                                          interval=float(self._ctx.config.get('watch_interval_sec', default=5)))
            self._watcher.start()

    def stop(self):
        thread = self._watcher.stop() if self._watcher else None
        self._index.close()
        return [thread] if thread else []

    def _schedule_scan(self) -> None:
        """Rescan in the background; requests during a running scan collapse into one follow-up."""
        if self._scan_pending.is_set():
            return
        self._scan_pending.set()

        def run():
            self._scan_pending.clear()
            try:
                result = self._index.scan()
            except Exception:
                logger.exception("Library scan failed")
                return
            self._ctx.publish(self.scanned, LibraryScanned(**vars(result)))

        self._executor.submit(run)

    def _refresh_all(self) -> Dict[str, Any]:
        self._schedule_scan()
        for name, source in self.sources.items():
            try:
                source.refresh()
            except Exception as error:
                raise LibraryError(502, 'library_update_failed', f"Could not update '{name}': {error}") from error
        return {'scanning': True}

    # -- sources --------------------------------------------------------------------------------

    def _source(self, provider: Optional[str]) -> Optional[LibrarySource]:
        """None stands for the local index."""
        if provider in (None, '', LOCAL_SOURCE):
            return None
        if provider not in self.sources:
            raise OperationError(404, 'unknown_source', f"Unknown library source '{provider}'")
        return self.sources.get(provider)

    def _local_source_info(self) -> SourceInfo:
        return SourceInfo(id=LOCAL_SOURCE, label='Local', views=[
            LibraryView(id='albums', label='Albums', kind='items', content_types=['album']),
            LibraryView(id='folders', label='Folders', kind='folders'),
        ])

    def _cover_url(self, relpath: Optional[str]) -> Optional[str]:
        if relpath is None:
            return None
        path = self._index.absolute(relpath)
        if path is None or not path.is_file():
            return None
        name = self._covers.cover_for(path)
        return f'{COVER_ROUTE}/{name}' if name else None

    def _local_song(self, data: Dict[str, Any]) -> Song:
        return Song(provider=LOCAL_SOURCE, file=data['path'], title=data['title'], artist=data['artist'],
                    album=data['album'], albumartist=data['albumartist'], track=data['track'],
                    duration=data['duration'])

    # -- file management (paths used by the web app) --------------------------------------------

    @query(path='/api/v1/library/entries')
    def list_entries(self, folder: str) -> LibraryEntries:
        """Files and folders in a library folder."""
        return LibraryEntries(entries=self._files.list_entries(folder))

    @action(path='/api/v1/library/folders', status_code=201)
    def create_folder(self, parent: str, name: str) -> CreatedFolder:
        """Create a folder in the library."""
        path = self._files.create_folder(parent, name)
        return CreatedFolder(path=path)

    @action(method='DELETE', path='/api/v1/library/entries')
    def delete_entries(self, paths: List[str]) -> DeletedEntries:
        """Delete files and folders from the library."""
        deleted = self._files.delete_entries(paths)
        self._schedule_scan()
        return DeletedEntries(deleted=deleted)

    @action(path='/api/v1/library/refresh')
    def refresh(self) -> ScanStarted:
        """Rescan the library (and refresh all other sources)."""
        self._refresh_all()
        return ScanStarted(scanning=True)

    def extra_routes(self, router) -> None:
        @router.put('/api/v1/library/files', status_code=201, tags=['library'])
        async def upload_file(request: Request, folder: str, name: str):
            """Upload one file (raw request body) into a library folder."""
            return await self._upload(request, folder, name)

        @router.get(COVER_ROUTE + '/{cover}', tags=['library'])
        async def cover_file(cover: str):
            path = self._covers.path(cover)
            if path is None:
                return JSONResponse(status_code=404, content={'error': {'code': 'unknown_cover', 'message': cover}})
            return FileResponse(path)

    async def _upload(self, request: Request, folder: str, name: str):
        content_length = request.headers.get('content-length')
        if content_length is not None and content_length.isdigit() and int(content_length) > MAX_UPLOAD_SIZE:
            return JSONResponse(status_code=413, content={'error': {
                'code': 'file_too_large', 'message': 'Files are limited to 1 GiB.'}})
        loop = asyncio.get_running_loop()
        try:
            upload = await loop.run_in_executor(self._file_executor, self._files.start_upload, folder, name)
        except LibraryError as error:
            return JSONResponse(status_code=error.status, content={'error': {'code': error.code, 'message': error.message}})
        try:
            async for chunk in request.stream():
                if chunk:
                    await loop.run_in_executor(self._file_executor, upload.write, chunk)
            await loop.run_in_executor(self._file_executor, upload.finish)
        except LibraryError as error:
            await loop.run_in_executor(self._file_executor, upload.abort)
            return JSONResponse(status_code=error.status, content={'error': {'code': error.code, 'message': error.message}})
        except Exception:
            await loop.run_in_executor(self._file_executor, upload.abort)
            raise
        self._schedule_scan()
        return JSONResponse(status_code=201, content={'path': upload.relative_path, 'size': upload.size})

    # -- browsing -------------------------------------------------------------------------------

    @query(path='/sources')
    def list_sources(self) -> List[SourceInfo]:
        """The local library and every registered source, with their views."""
        result = [self._local_source_info()]
        for name, source in self.sources.items():
            try:
                result.append(SourceInfo.model_validate(source.describe()))
            except Exception as error:
                logger.warning(f"Library source '{name}' could not describe itself: {error}")
        return result

    @query(path='/items')
    def list_items(self, provider: Optional[str] = None,
                   content_types: Optional[List[str]] = None) -> List[LibraryItem]:
        """Albums (and other items) of one source or all of them."""
        providers = [provider] if provider else [LOCAL_SOURCE, *self.sources.names()]
        items: List[LibraryItem] = []
        for name in providers:
            source = self._source(name)
            if source is None:
                if content_types is None or 'album' in content_types:
                    items.extend(LibraryItem(provider=LOCAL_SOURCE, albumartist=a['albumartist'], album=a['album'])
                                 for a in self._index.albums())
                continue
            try:
                items.extend(LibraryItem.model_validate({**item, 'provider': name})
                             for item in source.list_items(content_types) or [])
            except Exception as error:
                if provider:
                    raise
                logger.warning(f"Library source '{name}' is not available: {error}")
        return items

    @query(path='/songs')
    def list_songs(self, albumartist: str, album: str, content_uri: Optional[str] = None,
                   provider: Optional[str] = None) -> List[Song]:
        """Songs of an album, in track order."""
        source = self._source(provider)
        if source is None:
            return [self._local_song(song) for song in self._index.album_songs(albumartist or None, album)]
        return [song_from_source(provider, song) for song in source.list_songs(albumartist, album, content_uri) or []]

    @query(path='/song')
    def get_song(self, song_url: str, provider: Optional[str] = None) -> Optional[Song]:
        """Metadata of a single song, or null if it is unknown."""
        source = self._source(provider)
        if source is None:
            relpath = self._index.relative(song_url)
            song = self._index.song(relpath) if relpath else None
            return self._local_song(song) if song else None
        data = source.get_song(song_url)
        return song_from_source(provider, data) if data else None

    @query(path='/search')
    def search(self, query: str) -> List[Song]:
        """Songs of the local library matching title, artist, album or path."""
        return [self._local_song(song) for song in self._index.search(query)]

    @query(path='/cover/song')
    def get_song_cover(self, song_url: str, provider: Optional[str] = None) -> CoverArt:
        """Cover art URL of a song."""
        source = self._source(provider)
        if source is None:
            return CoverArt(cover_url=self._cover_url(self._index.relative(song_url)))
        return CoverArt(cover_url=source.cover(song_url))

    @query(path='/cover/album')
    def get_album_cover(self, albumartist: str, album: str, content_uri: Optional[str] = None,
                        provider: Optional[str] = None) -> CoverArt:
        """Cover art URL of an album (the cover of its first song)."""
        songs = self.list_songs(albumartist, album, content_uri, provider)
        if not songs:
            return CoverArt()
        return self.get_song_cover(songs[0].file, provider)

    @action(path='/covers/flush')
    def flush_covers(self) -> None:
        """Delete all cached cover art; it is extracted again when needed."""
        self._covers.flush()
