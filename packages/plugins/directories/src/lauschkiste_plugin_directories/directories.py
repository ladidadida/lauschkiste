"""The podcast directories: what each one is asked and how its answer is read."""

import hashlib
import time
from typing import Any, Callable, Dict, List, Optional

import requests

TIMEOUT = (5, 10)
USER_AGENT = 'Lauschkiste (podcast search)'

Row = Dict[str, Any]


class DirectoryError(Exception):
    pass


def get_json(url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Any:
    try:
        response = requests.get(url, params=params, headers={'User-Agent': USER_AGENT, **(headers or {})},
                                timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as error:
        raise DirectoryError(f'not reachable ({error.__class__.__name__})') from None
    try:
        return response.json()
    except ValueError:
        raise DirectoryError('the answer is not JSON') from None


class ITunes:
    """Apple Podcasts: ``/search`` and the top list, which only names the podcasts and needs a ``/lookup``."""

    def __init__(self, label: str, url: str = '', country: str = 'DE', **_):
        self.label = label
        self.base = (url or 'https://itunes.apple.com').rstrip('/')
        self.country = country.lower()

    def _rows(self, results: List[Row]) -> List[Row]:
        return [{'title': r.get('collectionName') or r.get('trackName'), 'feed_url': r.get('feedUrl'),
                 'author': r.get('artistName'), 'image': r.get('artworkUrl600') or r.get('artworkUrl100')}
                for r in results]

    def search(self, term: str, limit: int) -> List[Row]:
        data = get_json(f'{self.base}/search', {'term': term, 'media': 'podcast', 'entity': 'podcast',
                                                'country': self.country, 'limit': limit})
        return self._rows(data.get('results') or [])

    def top(self, limit: int) -> List[Row]:
        chart = get_json(f'{self.base}/{self.country}/rss/toppodcasts/limit={limit}/json')
        ids = [entry['id']['attributes']['im:id'] for entry in (chart.get('feed') or {}).get('entry') or []]
        if not ids:
            return []
        found = get_json(f'{self.base}/lookup', {'id': ','.join(ids), 'entity': 'podcast'}).get('results') or []
        by_id = {str(r.get('collectionId')): r for r in found}
        return self._rows([by_id[i] for i in ids if i in by_id])


class Fyyd:
    """fyyd, a German directory."""

    def __init__(self, label: str, url: str = '', language: str = 'de', **_):
        self.label = label
        self.base = (url or 'https://api.fyyd.de').rstrip('/')
        self.language = language

    @staticmethod
    def _rows(data: Any) -> List[Row]:
        return [{'title': r.get('title'), 'feed_url': r.get('xmlURL'), 'author': r.get('author'),
                 'image': r.get('imgURL') or r.get('layoutImageURL')} for r in (data or {}).get('data') or []]

    def search(self, term: str, limit: int) -> List[Row]:
        return self._rows(get_json(f'{self.base}/0.2/search/podcast', {'title': term, 'count': limit}))

    def top(self, limit: int) -> List[Row]:
        return self._rows(get_json(f'{self.base}/0.2/feature/podcast/hot',
                                   {'count': limit, 'language': self.language}))


class PodcastIndex:
    """The Podcast Index, which needs a (free) key and secret."""

    def __init__(self, label: str, url: str = '', language: str = 'de', key: Callable[[], str] = lambda: '',
                 secret: Callable[[], str] = lambda: '', **_):
        self.label = label
        self.base = (url or 'https://api.podcastindex.org').rstrip('/')
        self.language = language
        self._key, self._secret = key, secret

    def _headers(self) -> Dict[str, str]:
        key, secret = self._key(), self._secret()
        if not key or not secret:
            raise DirectoryError('needs an API key and secret (podcastindex.org)')
        now = str(int(time.time()))
        return {'X-Auth-Date': now, 'X-Auth-Key': key,
                'Authorization': hashlib.sha1((key + secret + now).encode()).hexdigest()}

    @staticmethod
    def _rows(data: Any) -> List[Row]:
        return [{'title': r.get('title'), 'feed_url': r.get('url'), 'author': r.get('author'),
                 'image': r.get('image') or r.get('artwork')} for r in (data or {}).get('feeds') or []]

    def search(self, term: str, limit: int) -> List[Row]:
        return self._rows(get_json(f'{self.base}/api/1.0/search/byterm', {'q': term, 'max': limit},
                                   self._headers()))

    def top(self, limit: int) -> List[Row]:
        return self._rows(get_json(f'{self.base}/api/1.0/podcasts/trending',
                                   {'max': limit, 'lang': self.language}, self._headers()))


#: kbit/s; above this a stream is video, not radio
MAX_BITRATE = 600


class RadioBrowser:
    """radio-browser.info, an open directory of internet radio stations (no key). The usual servers are tried
    one after the other."""

    SERVERS = ('https://de1.api.radio-browser.info', 'https://de2.api.radio-browser.info',
               'https://at1.api.radio-browser.info')

    def __init__(self, label: str, url: str = '', country: str = 'de', **_):
        self.label = label
        self.servers = (url.rstrip('/'),) if url else self.SERVERS
        self.country = country.upper()

    def _get(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        params = {'limit': 20, 'hidebroken': 'true', 'order': 'clickcount', 'reverse': 'true', **params}
        error: Optional[DirectoryError] = None
        for server in self.servers:
            try:
                data = get_json(f'{server}/json/stations/search', params)
            except DirectoryError as failed:
                error = failed
                continue
            return [row for row in data if isinstance(row, dict)] if isinstance(data, list) else []
        raise error or DirectoryError('no server')

    @staticmethod
    def _rows(rows: List[Dict[str, Any]]) -> List[Row]:
        result = []
        for row in rows:
            if int(row.get('bitrate') or 0) > MAX_BITRATE:
                continue  # TV and video streams appear in the directory, too
            logo = row.get('favicon') or ''
            result.append({
                'name': (row.get('name') or '').strip(), 'url': row.get('url_resolved') or row.get('url'),
                'logo': logo if logo.lower().startswith(('http://', 'https://')) else None,
                'country': row.get('countrycode') or None, 'tags': (row.get('tags') or '')[:60] or None,
                'codec': row.get('codec') or None, 'bitrate': row.get('bitrate') or None})
        return result

    def search(self, term: str, limit: int) -> List[Row]:
        """Stations whose name matches, then those with a matching tag (so that "kinder" finds children's radio)."""
        by_name = self._get({'name': term, 'limit': limit})
        by_tag = self._get({'tag': term, 'limit': limit})
        seen, merged = set(), []
        for row in by_name + by_tag:
            if row.get('stationuuid') not in seen:
                seen.add(row.get('stationuuid'))
                merged.append(row)
        return self._rows(merged[:limit])

    def top(self, limit: int) -> List[Row]:
        return self._rows(self._get({'countrycode': self.country, 'limit': limit}))
