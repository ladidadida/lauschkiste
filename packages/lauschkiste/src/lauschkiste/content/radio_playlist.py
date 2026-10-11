"""Station lists as ``.m3u`` and ``.pls`` files, which radio apps and players import and export."""

import re
from typing import Dict, Iterable, List
from urllib.parse import urlsplit

MAX_BYTES = 1024 * 1024


def _name_from(url: str) -> str:
    return urlsplit(url).netloc or url


def parse_stations(content: str) -> List[Dict[str, str]]:
    """``[{"name", "url"}]`` of every stream in an M3U (with names from its EXTINF lines) or PLS playlist.

    Raises ValueError if ``content`` has no stream or is too big."""
    if len(content.encode()) > MAX_BYTES:
        raise ValueError('the file is too big')
    stations: List[Dict[str, str]] = []
    if content.lstrip().lower().startswith('[playlist]'):
        files: Dict[str, str] = {}
        titles: Dict[str, str] = {}
        for line in content.splitlines():
            match = re.match(r'\s*(file|title)(\d+)\s*=\s*(.*)', line, re.IGNORECASE)
            if match:
                (files if match.group(1).lower() == 'file' else titles)[match.group(2)] = match.group(3).strip()
        for number in sorted(files, key=int):
            if files[number].lower().startswith(('http://', 'https://')):
                stations.append({'name': titles.get(number) or _name_from(files[number]), 'url': files[number]})
    else:
        name = ''
        for line in content.splitlines():
            line = line.strip()
            if line.upper().startswith('#EXTINF'):
                name = line.split(',', 1)[1].strip() if ',' in line else ''
            elif line.lower().startswith(('http://', 'https://')):
                stations.append({'name': name or _name_from(line), 'url': line})
                name = ''
    if not stations:
        raise ValueError('no stream found in the file')
    return stations


def render_m3u(stations: Iterable[Dict[str, str]]) -> str:
    """An extended M3U for ``{'name', 'url'}`` pairs."""
    lines = ['#EXTM3U']
    for station in stations:
        lines.append(f"#EXTINF:-1,{station['name']}")
        lines.append(station['url'])
    return '\n'.join(lines) + '\n'
