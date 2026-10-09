"""OPML, the list format podcast apps (AntennaPod and others) import and export their subscriptions with."""

import xml.etree.ElementTree as ElementTree
from typing import Dict, Iterable, List, Tuple
from urllib.parse import urlsplit, urlunsplit

MAX_BYTES = 2 * 1024 * 1024


def normalize_url(url: str) -> str:
    """A feed address for comparing: scheme and host in lower case, no fragment, no trailing slash."""
    parts = urlsplit(url.strip())
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip('/'), parts.query, ''))


def parse_opml(content: str) -> List[Dict[str, str]]:
    """``[{'title', 'url'}]`` of every feed in an OPML document (outlines may be nested in folders).

    Raises ValueError if ``content`` is not OPML."""
    if len(content.encode()) > MAX_BYTES:
        raise ValueError('the file is too big')
    try:
        root = ElementTree.fromstring(content.encode())
    except ElementTree.ParseError as error:
        raise ValueError(f'not a valid OPML file: {error}') from None
    if root.tag.lower() != 'opml':
        raise ValueError('not an OPML file')
    feeds = []
    for outline in root.iter('outline'):
        url = outline.get('xmlUrl') or outline.get('xmlurl')
        if url:
            feeds.append({'title': (outline.get('title') or outline.get('text') or '').strip(), 'url': url.strip()})
    return feeds


def render_opml(podcasts: Iterable[Tuple[str, str]], title: str = 'Lauschkiste') -> str:
    """OPML 2.0 for ``(name, feed address)`` pairs."""
    root = ElementTree.Element('opml', version='2.0')
    ElementTree.SubElement(ElementTree.SubElement(root, 'head'), 'title').text = title
    body = ElementTree.SubElement(root, 'body')
    for name, url in podcasts:
        ElementTree.SubElement(body, 'outline', type='rss', text=name, title=name, xmlUrl=url)
    return ElementTree.tostring(root, encoding='unicode', xml_declaration=False).join(
        ['<?xml version="1.0" encoding="UTF-8"?>\n', '\n'])
