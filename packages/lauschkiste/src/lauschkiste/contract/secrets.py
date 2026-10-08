"""Secrets (API keys, passwords) of modules, kept apart from the main configuration.

They live in ``secrets.yaml`` next to the configuration file, readable for the user only, under the
same key path as the setting (``plugins.<name>.<key>``). Modules read them through ``ctx.config`` as
if they were ordinary settings; the main configuration, which people share and back up, never holds them.
"""

import logging
import os
import threading
from pathlib import Path
from typing import Any, Optional

from ruamel.yaml import YAML

logger = logging.getLogger('lauschkiste.contract.secrets')

FILE_NAME = 'secrets.yaml'


def secrets_path(config_file: Optional[str]) -> Optional[Path]:
    return Path(config_file).parent / FILE_NAME if config_file else None


class SecretStore:
    def __init__(self, path: Optional[Path]):
        self.path = path
        self._lock = threading.Lock()
        self._data: dict = {}
        if path is not None and path.exists():
            try:
                loaded = YAML(typ='safe').load(path.read_text())
            except Exception as error:
                logger.error(f"Could not read '{path}': {error}")
                loaded = None
            self._data = loaded if isinstance(loaded, dict) else {}

    def get(self, *keys: str, default: Any = None) -> Any:
        with self._lock:
            node: Any = self._data
            for key in keys:
                if not isinstance(node, dict) or key not in node:
                    return default
                node = node[key]
            return node

    def set(self, *keys: str, value: Any) -> None:
        """Store a value and write the file; an empty value removes it."""
        with self._lock:
            node = self._data
            for key in keys[:-1]:
                node = node.setdefault(key, {})
            if value in ('', None):
                node.pop(keys[-1], None)
            else:
                node[keys[-1]] = value
            self._save()

    def _save(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + '.tmp')
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            with os.fdopen(fd, 'w') as stream:
                YAML(typ='safe').dump(self._data, stream)
            os.replace(tmp, self.path)
        finally:
            if tmp.exists():
                tmp.unlink()
