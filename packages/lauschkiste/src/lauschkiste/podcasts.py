"""The podcasts core module: podcast feeds, episodes streamed and continued where they stopped.

Subscribed podcasts are kept in ``podcasts.podcasts_file``, the episodes of each feed are cached in
``podcasts.cache_dir`` and fetched again when older than ``refresh_minutes``. The position is kept
per episode; an episode played to the end counts as heard.
"""

import hashlib
import logging
import re
import threading
import time
import unicodedata
import xml.etree.ElementTree as ElementTree
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field

import lauschkiste.paths
import lauschkiste.statefile as statefile
from lauschkiste.cache import CacheFile, CachePlan
from lauschkiste.contract import CoreModule, OperationError, action, event, query
from lauschkiste.resume import ResumeTracker

logger = logging.getLogger('lauschkiste.podcasts')

DEFAULT_PODCASTS_FILE = 'settings/podcasts.yaml'
DEFAULT_STATE_FILE = 'settings/podcast_positions.json'
DEFAULT_CACHE_DIR = 'cache/podcasts'
FEED_TIMEOUT_SEC = 15
FEED_MAX_BYTES = 10 * 1024 * 1024

ITUNES = '{http://www.itunes.com/dtds/podcast-1.0.dtd}'
ATOM = '{http://www.w3.org/2005/Atom}'


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


class PodcastsChanged(BaseModel):
    podcasts: List[Podcast]


class FeedError(Exception):
    pass


SOURCE = 'podcasts'


def cache_item(podcast: str, episode: str) -> str:
    return f'{podcast}~{episode}'


class EpisodeProvider:
    """``cache.providers`` entry ``podcasts``: an episode is the file of its feed entry."""

    def __init__(self, module):
        self._module = module

    def plan(self, item: str) -> CachePlan:
        podcast, _, episode = item.partition('~')
        found = next((e for e in self._module._feed(podcast).get('episodes') or [] if e['id'] == episode), None)
        if found is None:
            raise OperationError(404, 'unknown_episode', f"Podcast '{podcast}' has no episode '{episode}'")
        extension = Path(urlparse(found['url']).path).suffix.lower()
        name = self._module._get(podcast).get('name') or podcast
        return CachePlan(title=f"{name}: {found['title']}", files=[CacheFile(
            name=f"episode{extension if extension in ('.mp3', '.m4a', '.ogg', '.opus', '.aac', '.wav') else '.mp3'}",
            url=found['url'], duration=found.get('duration'))])

    def version(self, item: str):
        return None

    def removable(self, item: str) -> bool:
        podcast, _, episode = item.partition('~')
        return bool(self._module._resume.entries().get(f'{podcast}/{episode}', {}).get('finished'))


def _check_url(url: str) -> str:
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        raise OperationError(422, 'invalid_url', f"The feed URL must be an http(s) URL, got '{url}'")
    return url


def _slug(name: str) -> str:
    text = unicodedata.normalize('NFKD', name.replace('ß', 'ss')).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-') or 'podcast'


def _text(element, path: str) -> Optional[str]:
    found = element.find(path)
    if found is None or found.text is None:
        return None
    return found.text.strip() or None


def _duration(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    try:
        seconds = 0.0
        for part in value.strip().split(':'):
            seconds = seconds * 60 + float(part)
        return seconds
    except ValueError:
        return None


def _date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def _episode_id(guid: str) -> str:
    return hashlib.sha1(guid.encode()).hexdigest()[:12]


def parse_feed(content: bytes) -> Dict[str, Any]:
    """``{'title', 'image', 'episodes': [{'id', 'title', 'url', 'published', 'duration', 'image'}]}``,
    newest episode first. Raises FeedError if ``content`` is not an RSS or Atom feed with audio."""
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError as error:
        raise FeedError(f'not a valid feed: {error}') from None
    episodes = []
    if root.tag == 'rss':
        channel = root.find('channel')
        if channel is None:
            raise FeedError('RSS feed without channel')
        title = _text(channel, 'title')
        image = _text(channel, 'image/url')
        itunes_image = channel.find(f'{ITUNES}image')
        if itunes_image is not None and itunes_image.get('href'):
            image = itunes_image.get('href')
        for item in channel.findall('item'):
            enclosure = item.find('enclosure')
            url = enclosure.get('url') if enclosure is not None else None
            if not url:
                continue
            item_image = item.find(f'{ITUNES}image')
            episodes.append({
                'guid': _text(item, 'guid') or url,
                'title': _text(item, 'title') or url.rsplit('/', 1)[-1],
                'url': url.strip(),
                'published': _date(_text(item, 'pubDate')),
                'duration': _duration(_text(item, f'{ITUNES}duration')),
                'image': item_image.get('href') if item_image is not None else None,
            })
    elif root.tag == f'{ATOM}feed':
        title = _text(root, f'{ATOM}title')
        image = _text(root, f'{ATOM}logo') or _text(root, f'{ATOM}icon')
        for entry in root.findall(f'{ATOM}entry'):
            link = next((link for link in entry.findall(f'{ATOM}link') if link.get('rel') == 'enclosure'), None)
            url = link.get('href') if link is not None else None
            if not url:
                continue
            episodes.append({
                'guid': _text(entry, f'{ATOM}id') or url,
                'title': _text(entry, f'{ATOM}title') or url.rsplit('/', 1)[-1],
                'url': url.strip(),
                'published': _date(_text(entry, f'{ATOM}published') or _text(entry, f'{ATOM}updated')),
                'duration': None,
                'image': None,
            })
    else:
        raise FeedError('neither an RSS nor an Atom feed')
    for episode in episodes:
        episode['id'] = _episode_id(episode.pop('guid'))
    episodes.sort(key=lambda episode: episode['published'] or '', reverse=True)
    return {'title': title, 'image': image, 'episodes': episodes}


def fetch_feed(url: str) -> Dict[str, Any]:
    import requests
    try:
        with requests.get(url, timeout=FEED_TIMEOUT_SEC, stream=True) as response:
            response.raise_for_status()
            content = response.raw.read(FEED_MAX_BYTES + 1, decode_content=True)
    except requests.RequestException as error:
        raise FeedError(f'could not load {url}: {error}') from None
    if len(content) > FEED_MAX_BYTES:
        raise FeedError(f'{url} is larger than {FEED_MAX_BYTES // 1024 // 1024} MiB')
    return parse_feed(content)


class Podcasts(CoreModule):
    """Podcasts: subscribe to feeds, play episodes and continue them."""

    name = 'podcasts'
    interface_version = '2.0'
    concurrency = 'threadsafe'
    requires = ('player', 'cache')
    settings = PodcastSettings

    changed = event('changed', PodcastsChanged)

    def __init__(self):
        self._ctx: Any = None
        self._lock = threading.Lock()
        self._fetch_lock = threading.Lock()
        self._path = Path(DEFAULT_PODCASTS_FILE)
        self._cache_dir = Path(DEFAULT_CACHE_DIR)
        self._podcasts: Dict[str, Dict[str, Any]] = {}
        self._feeds: Dict[str, Dict[str, Any]] = {}
        self._refresh_sec = 3600.0
        self._max_episodes = 100
        self._resume: Any = None

    def start(self, ctx) -> None:
        self._ctx = ctx
        self._path = lauschkiste.paths.resolve(ctx.config.get('podcasts_file', default=DEFAULT_PODCASTS_FILE))
        self._cache_dir = lauschkiste.paths.resolve(ctx.config.get('cache_dir', default=DEFAULT_CACHE_DIR))
        self._refresh_sec = float(ctx.config.get('refresh_minutes', default=60)) * 60
        self._max_episodes = int(ctx.config.get('max_episodes', default=100))
        podcasts = statefile.read_yaml(self._path).get('podcasts') or {}
        self._podcasts = {str(key): dict(value) for key, value in podcasts.items()
                          if isinstance(value, dict) and value.get('url')} if isinstance(podcasts, dict) else {}
        for key in self._podcasts:
            self._feeds[key] = statefile.read_json(self._cache_file(key))
        self._resume = ResumeTracker(
            ctx, lauschkiste.paths.resolve(ctx.config.get('state_file', default=DEFAULT_STATE_FILE)),
            rewind_sec=float(ctx.config.get('rewind_sec', default=10)),
            save_interval_sec=float(ctx.config.get('save_interval_sec', default=10)))
        self._resume.start()
        ctx.modules.cache.providers.register(SOURCE, EpisodeProvider(self))

    def ready(self) -> None:
        self._publish()

    def stop(self):
        self._resume.stop()
        return []

    def settings_changed(self, changed):
        if 'refresh_minutes' in changed:
            self._refresh_sec = float(changed['refresh_minutes']) * 60
        if 'max_episodes' in changed:
            self._max_episodes = int(changed['max_episodes'])
        if 'rewind_sec' in changed:
            self._resume.configure(float(changed['rewind_sec']))
        return True

    # -- storage --------------------------------------------------------------------------------

    def _cache_file(self, podcast: str) -> Path:
        return self._cache_dir / f'{podcast}.json'

    def _store(self) -> None:
        with self._lock:
            data = {'podcasts': {key: {k: v for k, v in value.items() if v is not None}
                                 for key, value in self._podcasts.items()}}
        try:
            statefile.write_yaml(self._path, data)
        except OSError as error:
            raise OperationError(500, 'not_saved', f"Could not save the podcasts: {error}") from None

    def _fetch(self, podcast: str, url: str) -> Dict[str, Any]:
        """Fetch a feed and cache its episodes."""
        feed = fetch_feed(url)
        feed['episodes'] = feed['episodes'][:self._max_episodes]
        feed['fetched_at'] = time.time()
        with self._lock:
            if podcast in self._podcasts:
                self._feeds[podcast] = feed
                self._podcasts[podcast]['image'] = self._podcasts[podcast].get('image') or feed.get('image')
        try:
            statefile.write_json(self._cache_file(podcast), feed)
        except OSError as error:
            logger.warning(f"Could not cache the episodes of '{podcast}': {error}")
        return feed

    def _feed(self, podcast: str, refresh: bool = False) -> Dict[str, Any]:
        """The cached feed, fetched again when stale; the cache is used when fetching fails."""
        entry = self._get(podcast)
        with self._lock:
            feed = self._feeds.get(podcast) or {}
        if refresh or time.time() - float(feed.get('fetched_at') or 0) > self._refresh_sec:
            with self._fetch_lock:
                try:
                    feed = self._fetch(podcast, entry['url'])
                except FeedError as error:
                    if not feed.get('episodes'):
                        raise OperationError(502, 'feed_unavailable', f"Podcast '{podcast}': {error}") from None
                    logger.warning(f"Podcast '{podcast}': {error}; using the cached episodes")
        return feed

    # -- helpers --------------------------------------------------------------------------------

    def _get(self, podcast: str) -> Dict[str, Any]:
        with self._lock:
            entry = self._podcasts.get(podcast)
            if entry is None:
                raise OperationError(404, 'unknown_podcast', f"Unknown podcast '{podcast}'")
            return dict(entry)

    def _episodes(self, podcast: str, feed: Dict[str, Any]) -> List[Episode]:
        positions = self._resume.entries()
        cached = {entry.item for entry in self._ctx.modules.cache.cached(SOURCE)}
        result = []
        for data in feed.get('episodes') or []:
            position = positions.get(f"{podcast}/{data['id']}", {})
            heard = bool(position.get('finished'))
            elapsed = float(position.get('elapsed') or 0) if not heard else 0.0
            item = cache_item(podcast, data['id'])
            result.append(Episode(**data, item=item, availability='cached' if item in cached else 'stream',
                                  elapsed=elapsed, heard=heard))
        return result

    def _podcast(self, key: str) -> Podcast:
        entry = self._get(key)
        with self._lock:
            feed = dict(self._feeds.get(key) or {})
        episodes = self._episodes(key, feed)
        fetched_at = feed.get('fetched_at')
        return Podcast(id=key, name=entry.get('name') or key, url=entry['url'], image=entry.get('image'),
                       episodes=len(episodes), unheard=sum(1 for episode in episodes if not episode.heard),
                       updated_at=datetime.fromtimestamp(fetched_at, timezone.utc).isoformat() if fetched_at else None)

    def _list(self) -> List[Podcast]:
        with self._lock:
            keys = list(self._podcasts)
        return sorted((self._podcast(key) for key in keys), key=lambda podcast: podcast.name.casefold())

    def _publish(self) -> None:
        self._ctx.publish(self.changed, PodcastsChanged(podcasts=self._list()))

    # -- operations -----------------------------------------------------------------------------

    @query(path='/')
    def list_podcasts(self) -> List[Podcast]:
        """All podcasts, by name, with the number of (unheard) episodes."""
        return self._list()

    @query(path='/{podcast}/episodes')
    def list_episodes(self, podcast: str) -> List[Episode]:
        """Episodes of a podcast, newest first (the feed is fetched again when stale)."""
        return self._episodes(podcast, self._feed(podcast))

    @action(path='/', status_code=201)
    def add_podcast(self, url: str, name: Optional[str] = None) -> Podcast:
        """Subscribe to a feed; the name defaults to the feed's title."""
        url = _check_url(url)
        try:
            feed = fetch_feed(url)
        except FeedError as error:
            raise OperationError(422, 'invalid_feed', str(error)) from None
        name = str((name or '').strip() or feed.get('title') or url)
        with self._lock:
            base = _slug(name)
            key, number = base, 2
            while key in self._podcasts:
                key, number = f'{base}-{number}', number + 1
            self._podcasts[key] = {'name': name, 'url': url}
        self._store()
        with self._fetch_lock:
            try:
                self._fetch(key, url)
            except FeedError as error:
                logger.warning(f"Podcast '{key}': {error}")
        self._store()
        self._publish()
        return self._podcast(key)

    @action(method='PUT', path='/{podcast}')
    def update_podcast(self, podcast: str, name: str) -> Podcast:
        """Rename a podcast."""
        self._get(podcast)
        if not name.strip():
            raise OperationError(422, 'invalid_name', 'A podcast needs a name')
        with self._lock:
            self._podcasts[podcast]['name'] = name.strip()
        self._store()
        self._publish()
        return self._podcast(podcast)

    @action(method='DELETE', path='/{podcast}')
    def delete_podcast(self, podcast: str) -> None:
        """Unsubscribe from a podcast. Cards playing it stop working."""
        self._get(podcast)
        with self._lock:
            self._podcasts.pop(podcast, None)
            self._feeds.pop(podcast, None)
        self._store()
        self._cache_file(podcast).unlink(missing_ok=True)
        for entry in self._ctx.modules.cache.cached(SOURCE):
            if entry.item.startswith(f'{podcast}~'):
                self._ctx.modules.cache.remove(SOURCE, entry.item)
        self._publish()

    @action(path='/refresh')
    def refresh(self, podcast: Optional[str] = None) -> None:
        """Fetch the episodes of one podcast, or of all."""
        with self._lock:
            keys = [podcast] if podcast else list(self._podcasts)
        failed = []
        for key in keys:
            try:
                self._feed(key, refresh=True)
            except OperationError as error:
                if podcast:
                    raise
                failed.append(f'{key}: {error.message}')
        self._store()
        self._publish()
        if failed:
            logger.warning(f"Could not refresh: {'; '.join(failed)}")

    @action()
    def play(self, podcast: str, episode: Optional[str] = None) -> None:
        """Play an episode where it stopped; without ``episode`` the newest unheard one (or the
        newest, when all are heard)."""
        episodes = self._episodes(podcast, self._feed(podcast))
        if not episodes:
            raise OperationError(404, 'no_episodes', f"Podcast '{podcast}' has no episodes")
        if episode is None:
            chosen = next((e for e in episodes if not e.heard), episodes[0])
        else:
            chosen = next((e for e in episodes if e.id == episode), None)
            if chosen is None:
                raise OperationError(404, 'unknown_episode', f"Podcast '{podcast}' has no episode '{episode}'")
        name = self._get(podcast).get('name') or podcast
        local = self._ctx.modules.cache.files(SOURCE, cache_item(podcast, chosen.id))
        self._resume.play(f'{podcast}/{chosen.id}', [local.files[0].path if local else chosen.url],
                          names=[chosen.url], context={
            'kind': 'podcast', 'title': f'{name}: {chosen.title}', 'action': 'podcasts.play',
            'args': {'podcast': podcast, 'episode': chosen.id}})

    @action()
    def set_heard(self, podcast: str, episode: str, heard: bool = True) -> None:
        """Mark an episode as heard (or not); either way it starts from the beginning next time."""
        self._get(podcast)
        self._resume.set_finished(f'{podcast}/{episode}', heard)
        self._publish()
