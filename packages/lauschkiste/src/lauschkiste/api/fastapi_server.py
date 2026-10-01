# -*- coding: utf-8 -*-
"""FastAPI + uvicorn HTTP and WebSocket API server.

The sole browser-facing HTTP/WebSocket bridge. Serves health, the routes of the modules (see
lauschkiste.contract.routes), events-over-websocket and (see lauschkiste.api.webapp_static) the webapp's
static build + /logs -- this is the one thing reachable from the LAN, hence `api.bind_address`
defaulting to 0.0.0.0.

Handlers run on a multi-worker executor; each module guards itself (see the contract's threading
model), so a slow call doesn't serialize the rest of the API.
"""

import asyncio
import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

import lauschkiste.cfghandler
import lauschkiste.paths
import lauschkiste.publishing
from lauschkiste.api.events import EventBroker, MAX_MESSAGE_SIZE, parse_subscription_command
from lauschkiste.api.webapp_static import register_webapp_routes
from lauschkiste.contract.routes import build_router

logger = logging.getLogger('jb.api.fastapi_server')
cfg = lauschkiste.cfghandler.get_handler('lauschkiste')

API_EXECUTOR_WORKERS = 4

WEBAPP_DIR_ENV = lauschkiste.paths.ENV_PREFIX + 'WEBAPP_DIR'


def default_webapp_build_dir() -> Path:
    """``api.webapp_dir``, else ``$LAUSCHKISTE_WEBAPP_DIR``, else the web app shipped in the package,
    else the build directory of a source checkout."""
    configured = cfg.getn('api', 'webapp_dir', default=None) or lauschkiste.paths.getenv('WEBAPP_DIR')
    if configured:
        return Path(configured).expanduser().resolve()
    package = Path(__file__).resolve().parent.parent
    checkout_build = package.parents[3] / 'packages' / 'webapp' / 'build'
    if not (package / 'webapp').is_dir() and checkout_build.is_dir():
        return checkout_build
    return package / 'webapp'


def default_logs_dir() -> Path:
    return lauschkiste.paths.home() / 'logs'


class _WebSocketClient:
    """Adapts a FastAPI WebSocket to the EventBroker's `write_message` / `subscriptions` contract."""

    def __init__(self, websocket: WebSocket, loop: asyncio.AbstractEventLoop):
        self._websocket = websocket
        self._loop = loop
        self.subscriptions = set()

    def write_message(self, message):
        return asyncio.run_coroutine_threadsafe(self._websocket.send_json(message), self._loop)


class BodySizeLimit:
    """Reject request bodies above ``limit`` bytes with 413 (except for streaming upload paths)."""

    def __init__(self, app, limit: int, exempt_paths=()):
        self.app = app
        self.limit = limit
        self.exempt_paths = set(exempt_paths)

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['path'] in self.exempt_paths:
            return await self.app(scope, receive, send)
        headers = dict(scope.get('headers') or [])
        declared = headers.get(b'content-length')
        if declared is not None and declared.isdigit() and int(declared) > self.limit:
            return await self._reject(send)

        received = 0
        started = False

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message['type'] == 'http.request':
                received += len(message.get('body', b''))
                if received > self.limit:
                    raise _BodyTooLarge()
            return message

        async def tracking_send(message):
            nonlocal started
            if message['type'] == 'http.response.start':
                started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracking_send)
        except _BodyTooLarge:
            if not started:
                await self._reject(send)

    @staticmethod
    async def _reject(send):
        body = json.dumps({'error': {'code': 'request_too_large', 'message': 'Request body exceeds 1 MiB.'}})
        await send({'type': 'http.response.start', 'status': 413,
                    'headers': [(b'content-type', b'application/json')]})
        await send({'type': 'http.response.body', 'body': body.encode()})


class _BodyTooLarge(Exception):
    pass


def _is_same_origin(websocket: WebSocket) -> bool:
    """Reject cross-origin WebSocket handshakes, matching Tornado's default `check_origin`.

    Without this, any page in the browser could open a WebSocket to this API and read (or, via
    future write-capable topics, trigger) whatever it exposes -- classic cross-site WebSocket
    hijacking. Starlette/FastAPI don't check this by default, unlike Tornado's WebSocketHandler.
    """
    origin = websocket.headers.get('origin')
    if origin is None:
        # Non-browser clients (e.g. `jukebox debug sniff`) don't send Origin at all.
        return True
    origin_host = urlsplit(origin).netloc.lower()
    request_host = (websocket.headers.get('host') or '').lower()
    return origin_host == request_host


async def _handle_events_websocket(websocket: WebSocket, broker):
    if not _is_same_origin(websocket):
        await websocket.close(code=1008)
        return
    await websocket.accept()
    loop = asyncio.get_running_loop()
    client = _WebSocketClient(websocket, loop)
    broker.register(client)
    try:
        while True:
            command = await websocket.receive_json()
            try:
                command_type, topics = parse_subscription_command(command)
            except ValueError as error:
                await websocket.close(code=1008, reason=str(error))
                return
            if command_type == 'subscribe':
                broker.subscribe(client, topics)
            else:
                broker.unsubscribe(client, topics)
    except WebSocketDisconnect:
        pass
    finally:
        broker.unregister(client)


def create_app(broker, executor, modules=None, webapp_build_dir=None, logs_dir=None):
    app = FastAPI()
    app.add_middleware(BodySizeLimit, limit=MAX_MESSAGE_SIZE, exempt_paths={'/api/v1/library/files'})

    @app.get('/api/v1/health')
    async def health():
        return {'status': 'ok'}

    @app.websocket('/api/v1/events')
    async def events(websocket: WebSocket):
        await _handle_events_websocket(websocket, broker)

    if modules is not None:
        app.include_router(build_router(modules, executor))

    # Registered last so it never shadows the /api/v1/* routes above: FastAPI/Starlette tries
    # routes in registration order, and this includes a catch-all.
    register_webapp_routes(
        app,
        build_dir=webapp_build_dir or default_webapp_build_dir(),
        logs_dir=logs_dir or default_logs_dir(),
    )

    return app


class FastApiServer(threading.Thread):
    """Run the browser API on an isolated asyncio event loop."""

    def __init__(self, bind_address=None, port=None, bus=None, modules=None):
        super().__init__(name='FastApiServer', daemon=True)
        self.bind_address = bind_address or cfg.getn('api', 'bind_address', default='0.0.0.0')
        self.port = port if port is not None else cfg.getn('api', 'port', default=5556)
        self.bus = bus or lauschkiste.publishing.get_bus()
        self.broker = EventBroker(bus=self.bus)
        self.modules = modules
        self._ready = threading.Event()
        self._startup_error = None
        self._loop = None
        self._server = None
        self._executor = None

    def start_and_wait(self, timeout=120):
        """The timeout only catches a hung start; slow boards (Pi Zero) need well over 5 s."""
        self.start()
        if not self._ready.wait(timeout):
            raise TimeoutError('Timed out while starting FastAPI server.')
        if self._startup_error is not None:
            raise RuntimeError('Could not start FastAPI server.') from self._startup_error

    def run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._run_async())
        except Exception as error:
            self._startup_error = error
            logger.exception("FastAPI server failed")
            self._ready.set()
        finally:
            self._loop.close()

    async def _run_async(self):
        self._executor = ThreadPoolExecutor(max_workers=API_EXECUTOR_WORKERS, thread_name_prefix='FastApi')
        app = create_app(self.broker, self._executor, modules=self.modules)

        config = uvicorn.Config(app, host=self.bind_address, port=self.port, loop='none', log_config=None)
        self._server = uvicorn.Server(config)

        # broker.publish is called synchronously from whatever thread published (see
        # lauschkiste.publishing.bus.EventBus); it hands off to this server's event loop itself via
        # asyncio.run_coroutine_threadsafe (see _WebSocketClient.write_message), so no separate
        # subscriber loop/bridging is needed here -- unlike the old ZMQ SUB-socket version.
        self.bus.register(self.broker.publish)

        serve_task = asyncio.ensure_future(self._server.serve())
        while not self._server.started and not serve_task.done():
            await asyncio.sleep(0.01)
        if serve_task.done() and serve_task.exception() is not None:
            raise serve_task.exception()

        logger.info(f"FastAPI server listening on {self.bind_address}:{self.port}")
        self._ready.set()
        try:
            await serve_task
        finally:
            self.bus.unregister(self.broker.publish)
            self._executor.shutdown(wait=False, cancel_futures=True)

    def terminate(self, timeout=5):
        logger.info("Closing FastAPI server")
        if not self.is_alive():
            return
        self._ready.wait(timeout)
        if self._loop is not None and self._server is not None:
            self._loop.call_soon_threadsafe(self._request_shutdown)
        self.join(timeout)
        if self.is_alive():
            logger.warning("FastAPI server did not stop within the shutdown timeout")

    def _request_shutdown(self):
        self._server.should_exit = True
