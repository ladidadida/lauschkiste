"""Reading podcast feeds (RSS with the iTunes extensions)."""

import hashlib
import xml.etree.ElementTree as ElementTree
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, Optional

FEED_TIMEOUT_SEC = 15
FEED_MAX_BYTES = 10 * 1024 * 1024

ITUNES = '{http://www.itunes.com/dtds/podcast-1.0.dtd}'
ATOM = '{http://www.w3.org/2005/Atom}'


class FeedError(Exception):
    pass



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
