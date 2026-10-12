"""The data of the podcasts module: settings, podcasts, episodes, search results and events."""

from typing import Any, Dict, List, Optional, Protocol

from pydantic import BaseModel, Field


class PodcastSettings(BaseModel):
    refresh_minutes: int = Field(60, ge=5, le=1440, title='Fetch episodes again after (minutes)')
    max_episodes: int = Field(100, ge=10, le=1000, title='Episodes kept per podcast')
    rewind_sec: float = Field(10, ge=0, le=120, title='Go back when continuing (seconds)')


class Podcast(BaseModel):
    id: str
    name: str
    url: str
    image: Optional[str] = None
    episodes: int = 0
    unheard: int = 0
    updated_at: Optional[str] = None
    #: taken off the "continue" list; it comes back with a new episode or when one is heard
    hidden: bool = False


class Episode(BaseModel):
    id: str
    #: the item id at ``cache`` (the episode can be downloaded)
    item: str = ''
    #: 'stream' (played over the network) or 'cached' (downloaded to the box)
    availability: str = 'stream'
    title: str
    url: str
    published: Optional[str] = None
    duration: Optional[float] = None
    image: Optional[str] = None
    elapsed: float = 0.0
    heard: bool = False


class PodcastHit(BaseModel):
    """A podcast found in a directory."""
    title: str
    feed_url: str
    author: Optional[str] = None
    image: Optional[str] = None
    directory: str = ''
    subscribed: bool = False


class SearchResult(BaseModel):
    hits: List[PodcastHit]
    #: directory id -> why it gave no answer
    errors: Dict[str, str] = {}


class DirectoryInfo(BaseModel):
    id: str
    label: str


class ImportResult(BaseModel):
    added: List[str]
    already_subscribed: int = 0
    invalid: int = 0


class Opml(BaseModel):
    content: str


class PodcastDirectory(Protocol):
    """A place to find podcasts, registered at ``podcasts.directories`` by a plugin."""

    def search(self, term: str, limit: int) -> List[Dict[str, Any]]:
        """Podcasts matching ``term`` as mappings with ``title``, ``feed_url`` and optionally ``author``, ``image``."""

    def top(self, limit: int) -> List[Dict[str, Any]]:
        """Popular podcasts, same mappings."""


class PodcastsChanged(BaseModel):
    podcasts: List[Podcast]
