"""Small state files of core modules (JSON or YAML), written atomically."""

import io
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

from ruamel.yaml import YAML

logger = logging.getLogger('lauschkiste.statefile')


def write_text(path: Path, text: str) -> None:
    """Write ``text`` via a temporary file and rename it, so a crash never leaves a truncated file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f'.{path.name}-')
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def _read(path: Path, parse) -> Dict[str, Any]:
    """The mapping in ``path``; empty if the file is missing or unreadable (logged)."""
    try:
        data = parse(path.read_text())
    except FileNotFoundError:
        return {}
    except Exception as error:
        logger.error(f"Could not read '{path}': {error}")
        return {}
    if data is None:
        return {}
    if not isinstance(data, dict):
        logger.error(f"Ignoring '{path}': expected a mapping")
        return {}
    return data


def read_json(path: Path) -> Dict[str, Any]:
    return _read(path, json.loads)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    write_text(path, json.dumps(data, indent=2, sort_keys=True))


def read_yaml(path: Path) -> Dict[str, Any]:
    return _read(path, YAML(typ='safe').load)


def write_yaml(path: Path, data: Dict[str, Any]) -> None:
    yaml = YAML(typ='safe')
    yaml.default_flow_style = False
    yaml.allow_unicode = True
    stream = io.StringIO()
    yaml.dump(data, stream)
    write_text(path, stream.getvalue())
