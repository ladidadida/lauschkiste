"""The radio core module: internet radio stations, one per card.

Stations are kept in ``radio.stations_file``. A station URL may point to the stream itself or to an
``.m3u``/``.pls`` playlist, which is resolved to its first stream when the station is played.
"""

import logging
import re
import threading
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol
from urllib.parse import urlparse

from pydantic import BaseModel

import lauschkiste.directories as directories
import lauschkiste.paths
import lauschkiste.statefile as statefile
from lauschkiste.contract import CoreModule, OperationError, action, event, extension_point, query
from lauschkiste.podcast_opml import normalize_url
from lauschkiste.radio_playlist import parse_stations, render_m3u

logger = logging.getLogger('lauschkiste.radio')

DEFAULT_STATIONS_FILE = 'settings/radio.yaml'
PLAYLIST_SUFFIXES = ('.m3u', '.pls')
PLAYLIST_TIMEOUT_SEC = 10
PLAYLIST_MAX_BYTES = 64 * 1024


class Station(BaseModel):
    id: str
    name: str
    url: str
    logo: Optional[str] = None


class StationHit(BaseModel):
    """A station found in a directory."""
    name: str
    url: str
    logo: Optional[str] = None
    country: Optional[str] = None
    tags: Optional[str] = None
    codec: Optional[str] = None
    bitrate: Optional[int] = None
    directory: str = ''
    #: already one of the stations
    added: bool = False


class SearchResult(BaseModel):
    hits: List[StationHit]
    #: directory id -> why it gave no answer
    errors: Dict[str, str] = {}


class DirectoryInfo(BaseModel):
    id: str
    label: str


class ImportResult(BaseModel):
    added: List[str]
    already_there: int = 0
    invalid: int = 0


class Playlist(BaseModel):
    content: str


class RadioDirectory(Protocol):
    """A place to find stations, registered at ``radio.directories`` by a plugin."""

    def search(self, term: str, limit: int) -> List[Dict[str, Any]]:
        """Stations matching ``term`` as mappings with ``name`` and ``url``, optionally ``logo``, ``country``, ``tags``,
        ``codec`` and ``bitrate``."""

    def top(self, limit: int) -> List[Dict[str, Any]]:
        """Popular stations, same mappings."""


class StationsChanged(BaseModel):
    stations: List[Station]


def _check_url(url: str, what: str) -> str:
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        raise OperationError(422, 'invalid_url', f"{what} must be an http(s) URL, got '{url}'")
    return url


def _slug(name: str) -> str:
    text = unicodedata.normalize('NFKD', name.replace('ß', 'ss')).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-') or 'station'


def streams_in_playlist(text: str) -> List[str]:
    """Stream URLs of an ``.m3u`` or ``.pls`` playlist, in order."""
    urls = []
    for line in text.splitlines():
        line = line.strip()
        if line.lower().startswith('file') and '=' in line:
            line = line.split('=', 1)[1].strip()
        if line.startswith(('http://', 'https://')):
            urls.append(line)
    return urls


class Radio(CoreModule):
    """Internet radio stations."""

    name = 'radio'
    interface_version = '2.0'
    concurrency = 'threadsafe'
    requires = ('player',)

    changed = event('changed', StationsChanged)
    directories = extension_point('directories', RadioDirectory)

    def __init__(self):
        self._ctx: Any = None
        self._lock = threading.Lock()
        self._path = Path(DEFAULT_STATIONS_FILE)
        self._stations: Dict[str, Dict[str, Any]] = {}

    def start(self, ctx) -> None:
        self._ctx = ctx
        self._path = lauschkiste.paths.resolve(ctx.config.get('stations_file', default=DEFAULT_STATIONS_FILE))
        stations = statefile.read_yaml(self._path).get('stations') or {}
        if not isinstance(stations, dict):
            logger.error(f"Ignoring stations in '{self._path}': expected a mapping of station ids")
            stations = {}
        self._stations = {str(key): dict(value) for key, value in stations.items()
                          if isinstance(value, dict) and value.get('url')}

    def ready(self) -> None:
        self._publish()

    def stop(self):
        return []

    # -- helpers --------------------------------------------------------------------------------

    def _list(self) -> List[Station]:
        with self._lock:
            stations = [Station(id=key, name=value.get('name') or key, url=value['url'], logo=value.get('logo'))
                        for key, value in self._stations.items()]
        return sorted(stations, key=lambda station: station.name.casefold())

    def _publish(self) -> None:
        self._ctx.publish(self.changed, StationsChanged(stations=self._list()))

    def _store(self) -> None:
        with self._lock:
            data = {'stations': {key: {k: v for k, v in value.items() if v is not None}
                                 for key, value in self._stations.items()}}
        try:
            statefile.write_yaml(self._path, data)
        except OSError as error:
            raise OperationError(500, 'not_saved', f"Could not save the stations: {error}") from None
        self._publish()

    def _get(self, station: str) -> Station:
        for entry in self._list():
            if entry.id == station:
                return entry
        raise OperationError(404, 'unknown_station', f"Unknown radio station '{station}'")

    def _stream_url(self, url: str) -> str:
        if not urlparse(url).path.lower().endswith(PLAYLIST_SUFFIXES):
            return url
        import requests
        try:
            with requests.get(url, timeout=PLAYLIST_TIMEOUT_SEC, stream=True) as response:
                response.raise_for_status()
                content = response.raw.read(PLAYLIST_MAX_BYTES, decode_content=True)
        except requests.RequestException as error:
            raise OperationError(502, 'playlist_unavailable', f"Could not load the playlist '{url}': {error}") from None
        streams = streams_in_playlist(content.decode('utf-8', errors='replace'))
        if not streams:
            raise OperationError(502, 'empty_playlist', f"No stream in the playlist '{url}'")
        return streams[0]

    # -- operations -----------------------------------------------------------------------------

    @query(path='/stations')
    def list_stations(self) -> List[Station]:
        """All stations, by name."""
        return self._list()

    @action(path='/stations', status_code=201)
    def add_station(self, name: str, url: str, logo: Optional[str] = None) -> Station:
        """Add a station; its id is derived from the name."""
        name = name.strip()
        if not name:
            raise OperationError(422, 'invalid_name', 'A station needs a name')
        url = _check_url(url, 'The station URL')
        logo = _check_url(logo, 'The logo') if logo else None
        with self._lock:
            base = _slug(name)
            key, number = base, 2
            while key in self._stations:
                key, number = f'{base}-{number}', number + 1
            self._stations[key] = {'name': name, 'url': url, 'logo': logo}
        self._store()
        return self._get(key)

    @action(method='PUT', path='/stations/{station}')
    def update_station(self, station: str, name: Optional[str] = None, url: Optional[str] = None,
                       logo: Optional[str] = None) -> Station:
        """Change a station; fields left out stay unchanged, an empty ``logo`` removes the logo."""
        self._get(station)
        changes: Dict[str, Any] = {}
        if name is not None:
            if not name.strip():
                raise OperationError(422, 'invalid_name', 'A station needs a name')
            changes['name'] = name.strip()
        if url is not None:
            changes['url'] = _check_url(url, 'The station URL')
        if logo is not None:
            changes['logo'] = _check_url(logo, 'The logo') if logo.strip() else None
        with self._lock:
            self._stations[station].update(changes)
        self._store()
        return self._get(station)

    @action(method='DELETE', path='/stations/{station}')
    def delete_station(self, station: str) -> None:
        """Delete a station. Cards playing it stop working."""
        self._get(station)
        with self._lock:
            self._stations.pop(station, None)
        self._store()

    # -- finding, importing and exporting stations ------------------------------------------------

    def _known_urls(self) -> set:
        with self._lock:
            return {normalize_url(value['url']) for value in self._stations.values()}

    def _ask(self, directory: Optional[str], call) -> SearchResult:
        answers, errors = directories.ask(self.directories.items(), directory, call, 'radio')
        known = self._known_urls()
        rows = directories.interleave(answers, lambda row: normalize_url(row['url']),
                                      lambda row: bool(row.get('name') and row.get('url')))
        hits = [StationHit(**{k: v for k, v in row.items() if k in StationHit.model_fields},
                           added=normalize_url(row['url']) in known) for row in rows]
        return SearchResult(hits=hits, errors=errors)

    @query(path='/directories')
    def list_directories(self) -> List[DirectoryInfo]:
        """The places stations can be searched in (added by plugins)."""
        return [DirectoryInfo(id=key, label=getattr(item, 'label', key)) for key, item in self.directories.items()]

    @query(path='/search')
    def search(self, term: str, directory: Optional[str] = None, limit: int = 20) -> SearchResult:
        """Search the directories for stations."""
        term = term.strip()
        if not term:
            return SearchResult(hits=[])
        return self._ask(directory, lambda item: item.search(term, max(1, min(limit, 50))))

    @query(path='/top')
    def top(self, directory: Optional[str] = None, limit: int = 20) -> SearchResult:
        """Popular stations of the directories."""
        return self._ask(directory, lambda item: item.top(max(1, min(limit, 50))))

    @action(path='/import_playlist')
    def import_playlist(self, content: str) -> ImportResult:
        """Add all streams of an M3U or PLS file as stations; known addresses are skipped."""
        try:
            entries = parse_stations(content)
        except ValueError as error:
            raise OperationError(422, 'invalid_playlist', str(error)) from None
        added, known, skipped, invalid = [], self._known_urls(), 0, 0
        with self._lock:
            for entry in entries:
                try:
                    url = _check_url(entry['url'], 'The station URL')
                except OperationError:
                    invalid += 1
                    continue
                if normalize_url(url) in known:
                    skipped += 1
                    continue
                known.add(normalize_url(url))
                base = _slug(entry['name'])
                key, number = base, 2
                while key in self._stations:
                    key, number = f'{base}-{number}', number + 1
                self._stations[key] = {'name': entry['name'], 'url': url}
                added.append(entry['name'])
        if added:
            self._store()
        return ImportResult(added=added, already_there=skipped, invalid=invalid)

    @query(path='/export_playlist')
    def export_playlist(self) -> Playlist:
        """The stations as an M3U file."""
        return Playlist(content=render_m3u({'name': s.name, 'url': s.url} for s in self._list()))

    @action()
    def play(self, station: str) -> None:
        """Play a station."""
        entry = self._get(station)
        self._ctx.modules.player.play_files([self._stream_url(entry.url)], context={
            'kind': 'radio', 'title': entry.name, 'action': 'radio.play', 'args': {'station': station}})
