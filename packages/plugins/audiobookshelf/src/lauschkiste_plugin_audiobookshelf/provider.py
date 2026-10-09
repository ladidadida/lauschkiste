"""The books of the server as items of the download cache."""

from typing import Optional

from lauschkiste.cache import CacheFile, CachePlan
from lauschkiste.contract import OperationError
from lauschkiste_plugin_audiobookshelf.client import AudiobookshelfError


class AudiobookshelfProvider:
    """``cache.providers`` entry ``audiobookshelf``: a book is all its audio files."""

    def __init__(self, source):
        self._source = source

    def plan(self, item: str) -> CachePlan:
        client = self._source.client()
        try:
            book = client.item(item)
        except AudiobookshelfError as error:
            raise OperationError(503, 'audiobookshelf_unavailable', str(error)) from None
        if book is None:
            raise OperationError(404, 'unknown_audiobook', f"No audiobook '{item}' on the Audiobookshelf server")
        media = book.get('media') or {}
        audio = sorted(media.get('audioFiles') or [], key=lambda f: f.get('index', 0))
        files = [CacheFile(name=f"{number:03d}_{entry['ino']}{entry['metadata'].get('ext') or ''}",
                           url=f"{client.base}/api/items/{item}/file/{entry['ino']}/download",
                           size=int(entry['metadata']['size']), duration=entry.get('duration'),
                           headers=client.headers)
                 for number, entry in enumerate(audio, 1)]
        return CachePlan(title=(media.get('metadata') or {}).get('title') or item,
                         version=str(book.get('updatedAt')) if book.get('updatedAt') is not None else None,
                         files=files)

    def version(self, item: str) -> Optional[str]:
        known = next((i for i in self._source.known_items() if i.get('id') == item), None)
        return str(known['updatedAt']) if known and known.get('updatedAt') is not None else None

    def removable(self, item: str) -> bool:
        entry = self._source.ledger.get(item) if self._source.ledger else None
        return bool(entry and entry.get('finished'))
