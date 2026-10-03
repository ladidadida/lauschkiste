"""Samba share of the library, switched on and off and given a password from the web app.

Samba itself is installed by ``lauschctl setup samba``; this plugin manages the share block in
``/etc/samba/smb.conf`` and the Samba password of the user Lauschkiste runs as (through
``sudo -n``, so it needs password-less sudo as on Raspberry Pi OS).
"""

import logging
import socket
import threading
from typing import Any, Optional

from fastapi.responses import JSONResponse
from pydantic import BaseModel

import lauschkiste.library
from lauschkiste.contract import OperationError, Plugin, action, query
from lauschkiste_cli.setup import samba
from lauschkiste_cli.setup.system import SetupError, System

logger = logging.getLogger('lauschkiste.samba')


class SambaStatus(BaseModel):
    installed: bool
    shared: bool
    outdated: bool
    has_password: bool
    user: str
    path: str
    address: Optional[str] = None


class SambaPassword(BaseModel):
    password: str


class Samba(Plugin):
    """Share the library on the network (Samba) and set its password."""

    name = 'samba'
    interface_version = '1.0'

    def __init__(self):
        self._system: Any = None
        self._lock = threading.Lock()

    def start(self, ctx) -> None:
        self._system = System()
        self._system.sudo = ['sudo', '-n']

    def _status(self) -> SambaStatus:
        system = self._system
        path = lauschkiste.library.root()
        installed = samba.installed(system)
        block = samba.current_block(system) if installed else None
        return SambaStatus(installed=installed, shared=block is not None,
                           outdated=block is not None and not samba.is_current(system, path),
                           has_password=installed and samba.has_user(system), user=system.user, path=path,
                           address=f'smb://{socket.gethostname()}/{samba.SHARE}' if block is not None else None)

    def _run(self, change) -> SambaStatus:
        with self._lock:
            if not samba.installed(self._system):
                raise OperationError(409, 'samba_not_installed',
                                     "Samba is not installed; run 'lauschctl setup samba' on the box")
            try:
                change()
            except SetupError as error:
                raise OperationError(500, 'samba_failed', f'{error} (password-less sudo is needed)') from None
            return self._status()

    @query(path='/status')
    def get_status(self) -> SambaStatus:
        """Whether Samba is installed, the library shared and a password set."""
        return self._status()

    @action(path='/share')
    def set_share(self, enabled: bool = True) -> SambaStatus:
        """Share the library on the network, or stop sharing it."""
        def change():
            if enabled:
                samba.share(self._system, lauschkiste.library.root())
            else:
                samba.unshare(self._system)
        return self._run(change)

    def extra_routes(self, router) -> None:
        @router.put('/api/v1/samba/password', tags=['samba'])
        def set_password(body: SambaPassword):
            """Set the Samba password of the user Lauschkiste runs as (at least 8 characters)."""
            def change():
                try:
                    samba.set_password(self._system, body.password)
                except ValueError as error:
                    raise OperationError(422, 'invalid_password', str(error)) from None
            try:
                return self._run(change)
            except OperationError as error:
                return JSONResponse(status_code=error.status,
                                    content={'error': {'code': error.code, 'message': error.message}})
