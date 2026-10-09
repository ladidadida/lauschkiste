# -*- coding: utf-8 -*-
"""Serve the built webapp, its fallback pages, and the /logs directory directly from FastAPI.

Serves the webapp's static build, a "build missing"/generic-404 fallback page and a /logs
directory listing. Unknown paths get the 404 page; there is no SPA deep-link fallback to index.html.
"""

import html
import logging
from pathlib import Path

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse, PlainTextResponse, Response
from starlette.staticfiles import StaticFiles

logger = logging.getLogger('lauschkiste.api.webapp_static')

NO_BUILD_HTML = """<html><body><h2>The Web App bundle is missing</h2>
<p>Lauschkiste requires a pre-built bundle. See
<a href="https://github.com/ladidadida/lauschkiste/blob/main/documentation/developers/webapp.md">
the Web App documentation</a> for how to build/install one.</p></body></html>"""

NOT_FOUND_HTML = """<html><body><h2>Not found</h2>
<p><a href="/">Web App</a> &middot; <a href="/logs">Log files</a></p></body></html>"""


#: Vite puts content-hashed files here; a new build gives them new names.
HASHED_ASSETS_DIR = 'assets'
CACHE_FOREVER = 'public, max-age=31536000, immutable'
#: Everything else keeps its name across versions, and packaged files all carry the same
#: modification time, so neither heuristic caching nor revalidation would notice an update.
CACHE_NEVER = 'no-store'


def _serve_html(path: Path, fallback_html: str, status_code: int = 200) -> Response:
    if path.is_file():
        return FileResponse(path, media_type='text/html', headers={'Cache-Control': CACHE_NEVER})
    return HTMLResponse(fallback_html, status_code=status_code)


def register_webapp_routes(app: FastAPI, *, build_dir: Path, logs_dir: Path) -> None:
    """Mount the webapp build's static assets, index.html, a generic 404, and /logs. Call once."""

    static_dir = build_dir / 'static'
    if static_dir.is_dir():
        app.mount('/static', StaticFiles(directory=static_dir), name='webapp-static')

    @app.get('/logs')
    async def list_logs():
        if not logs_dir.is_dir():
            return HTMLResponse('<html><body><p>No logs directory.</p></body></html>', status_code=404)
        entries = sorted(p.name for p in logs_dir.iterdir() if p.is_file())
        items = ''.join(f'<li><a href="/logs/{html.escape(name)}">{html.escape(name)}</a></li>' for name in entries)
        return HTMLResponse(f'<html><body><h2>shared/logs</h2><ul>{items}</ul></body></html>')

    @app.get('/logs/{filename}')
    async def get_log_file(filename: str):
        # Log filenames only (no path separators), served flat from logs_dir -- not a general
        # file server, so reject anything that isn't a plain filename in that directory.
        if '/' in filename or '\\' in filename or filename in ('.', '..'):
            return PlainTextResponse('Not found', status_code=404)
        path = logs_dir / filename
        if not path.is_file():
            return PlainTextResponse('Not found', status_code=404)
        return FileResponse(path, media_type='text/plain')

    @app.get('/')
    async def webapp_index():
        return _serve_html(build_dir / 'index.html', NO_BUILD_HTML)

    @app.get('/index.html')
    async def webapp_index_html():
        return _serve_html(build_dir / 'index.html', NO_BUILD_HTML)

    # Registered last: anything else the webapp build ships at its root (favicon, manifest,
    # locales/*, ...) if the exact file exists, else the generic 404 page (no SPA deep-link fallback).
    @app.get('/{path:path}')
    async def webapp_catch_all(request: Request, path: str):
        candidate = (build_dir / path).resolve()
        try:
            candidate.relative_to(build_dir.resolve())
        except ValueError:
            return HTMLResponse(NOT_FOUND_HTML, status_code=404)
        if candidate.is_file():
            hashed = path.split('/', 1)[0] == HASHED_ASSETS_DIR
            return FileResponse(candidate, headers={'Cache-Control': CACHE_FOREVER if hashed else CACHE_NEVER})
        return HTMLResponse(NOT_FOUND_HTML, status_code=404)
