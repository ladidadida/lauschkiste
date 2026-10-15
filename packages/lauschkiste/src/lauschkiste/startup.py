"""Start-up helpers for small boards."""

import importlib


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
