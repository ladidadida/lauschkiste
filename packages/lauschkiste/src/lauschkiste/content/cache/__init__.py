"""What a content provider tells the cache: the files of an item (``CachePlan``) and how to ask about it."""

from typing import Dict, List, Optional, Protocol

from pydantic import BaseModel, Field


class CacheFile(BaseModel):
    name: str
    url: str
    #: bytes; 0 when the source does not know (the size is then taken from the download)
    size: int = 0
    duration: Optional[float] = None
    headers: Dict[str, str] = {}


class CachePlan(BaseModel):
    title: str = ''
    version: Optional[str] = None
    files: List[CacheFile]


class CacheProvider(Protocol):
    def plan(self, item: str) -> CachePlan:
        """The files that make up an item, with the headers to fetch them; raises :class:`OperationError`."""

    def version(self, item: str) -> Optional[str]:
        """A value that changes when the server's copy of the item changes (from what is already known; no request)."""

    def removable(self, item: str) -> bool:
        """Whether the item may be removed to make room (for example finished or heard). Never for one in progress."""
