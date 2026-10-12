"""The data of the radio module: stations, search results, playlists and events."""

from typing import Any, Dict, List, Optional, Protocol

from pydantic import BaseModel


class Station(BaseModel):
    id: str
    name: str
    url: str
    logo: Optional[str] = None
    #: when it was last played (UTC); empty for a station never played here or taken off the "continue" list
    last_played: Optional[str] = None


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
