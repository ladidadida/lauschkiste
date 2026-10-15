"""Start-up helpers for small boards."""

import importlib
import os
import time
from typing import List, Optional, Tuple

_marks: List[Tuple[str, float]] = []


def process_age() -> Optional[float]:
    """Seconds since this process was started, None where /proc is not available."""
    try:
        with open('/proc/self/stat') as stream:
            started = int(stream.read().rsplit(')', 1)[1].split()[19]) / os.sysconf('SC_CLK_TCK')
        with open('/proc/uptime') as stream:
            return max(float(stream.read().split()[0]) - started, 0.0)
    except (OSError, ValueError, IndexError):
        return None


def mark(name: str) -> None:
    """Record that a start-up step is finished."""
    _marks.append((name, time.perf_counter()))


def _uptime() -> Optional[float]:
    try:
        with open('/proc/uptime') as stream:
            return float(stream.read().split()[0])
    except (OSError, ValueError, IndexError):
        return None


def timeline() -> str:
    """The recorded steps with their durations, and when the box was ready: seconds after boot where known."""
    if not _marks:
        return ''
    now = time.perf_counter()
    steps = [f"{name} {at - before:.1f} s" for (_, before), (name, at) in zip(_marks, _marks[1:])]
    age = process_age()
    if age is not None:
        steps.insert(0, f"Python and {_marks[0][0]} {age - (now - _marks[0][1]):.1f} s")
    else:
        steps.insert(0, _marks[0][0])
    text = f"Start-up: {', '.join(steps)}; total {(age if age is not None else now - _marks[0][1]):.1f} s"
    uptime = _uptime()
    return text if uptime is None else f"{text}, ready at boot + {uptime:.1f} s"


def import_fastapi() -> None:
    """Import FastAPI with the schemas of its OpenAPI models built on first use instead of now.

    They are only needed for ``/openapi.json``; building them at import takes seconds on a Pi Zero.
    """
    try:
        from pydantic._internal import _config
        defaults = _config.config_defaults
    except (ImportError, AttributeError):
        importlib.import_module('fastapi')
        return
    previous = defaults.get('defer_build', False)
    defaults['defer_build'] = True
    try:
        importlib.import_module('fastapi')
    finally:
        defaults['defer_build'] = previous
