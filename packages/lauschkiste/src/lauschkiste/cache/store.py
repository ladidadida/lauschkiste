"""The folder of downloaded items: ``<root>/<source>/<item>/``."""

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

#: Files of the cache machinery itself; they do not count as used space
INTERNAL = ('plan.json', 'status.json', 'meta.json')


class CacheStore:
    def __init__(self, root: Path):
        self.root = root
        self.rate_file = root / '.rate'

    def directory(self, source: str, item: str) -> Path:
        return self.root / source / item

    def _read(self, source: str, item: str, name: str) -> Optional[Dict[str, Any]]:
        try:
            data = json.loads((self.directory(source, item) / name).read_text())
        except (OSError, ValueError):
            return None
        return data if isinstance(data, dict) else None

    def meta(self, source: str, item: str) -> Optional[Dict[str, Any]]:
        return self._read(source, item, 'meta.json')

    def complete(self, source: str, item: str) -> Optional[Dict[str, Any]]:
        """The metadata of a complete download whose files are all there, else None."""
        meta = self.meta(source, item)
        if not meta or not meta.get('files'):
            return None
        for entry in meta['files']:
            path = self.directory(source, item) / entry['name']
            if not path.exists() or path.stat().st_size != entry['size']:
                return None
        return meta

    def status_of(self, source: str, item: str) -> Dict[str, Any]:
        return self._read(source, item, 'status.json') or {}

    def items(self, source: Optional[str] = None) -> List[Tuple[str, str]]:
        """``(source, item)`` of every folder, complete or not."""
        try:
            sources = [source] if source else sorted(entry.name for entry in self.root.iterdir() if entry.is_dir())
            return [(name, entry.name) for name in sources
                    for entry in sorted((self.root / name).iterdir()) if entry.is_dir()]
        except OSError:
            return []

    def used_bytes(self) -> int:
        total = 0
        for source, item in self.items():
            for path in self.directory(source, item).iterdir():
                if path.is_file() and path.name not in INTERNAL:
                    total += path.stat().st_size
        return total

    def partial_bytes(self, source: str, item: str) -> int:
        return sum(path.stat().st_size for path in self.directory(source, item).glob('*.part'))

    def remove(self, source: str, item: str) -> None:
        shutil.rmtree(self.directory(source, item), ignore_errors=True)

    def free_bytes(self) -> int:
        self.root.mkdir(parents=True, exist_ok=True)
        return shutil.disk_usage(self.root).free

    def set_rate(self, kbps: float) -> None:
        """The speed limit of the worker in kB/s: 0 none, -1 wait."""
        self.root.mkdir(parents=True, exist_ok=True)
        self.rate_file.write_text(str(int(kbps)))
