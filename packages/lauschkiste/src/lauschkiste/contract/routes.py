"""FastAPI routes generated from module operations, plus ``GET /api/v1/modules``."""

import asyncio
import inspect
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Path, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, create_model

import lauschkiste.contract.plugins as plugins
from lauschkiste.contract.declarations import Operation
from lauschkiste.contract.errors import ActionError, OperationError
from lauschkiste.contract.manager import ModuleHandle, ModuleManager

logger = logging.getLogger('lauschkiste.contract.routes')


class SettingsUpdate(BaseModel):
    values: Dict[str, Any]


class PluginState(BaseModel):
    enabled: bool


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={'error': {'code': code, 'message': message}})


async def _run(executor, handle: ModuleHandle, op: Operation, kwargs: Dict[str, Any]):
    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(executor, lambda: handle.invoke(op.name, **kwargs))
    except NotImplementedError as error:
        raise HTTPException(status_code=501, detail=str(error)) from error
    except OperationError as error:
        return _error(error.status, error.code, error.message)
    except ActionError as error:
        return _error(422, 'invalid_action', str(error))
    if result is None and op.returns_nothing:
        return Response(status_code=op.spec.status_code or 204)
    if op.spec.status_code is not None:
        return JSONResponse(status_code=op.spec.status_code, content=jsonable_encoder(result))
    return result


def _endpoint(executor, handle: ModuleHandle, op: Operation):
    path_params = op.path_params(handle.is_core)
    params: List[inspect.Parameter] = []
    for p in op.params:
        default = ... if p.default is inspect.Parameter.empty else p.default
        if p.name in path_params:
            marker = Path(...)
        elif op.kind == 'query':
            marker = Query(default)
        else:
            continue
        params.append(inspect.Parameter(p.name, inspect.Parameter.KEYWORD_ONLY,
                                        default=marker, annotation=op.param_types[p.name]))

    body_fields = [p for p in op.params if p.name not in path_params] if op.kind == 'action' else []
    body_model = op.args_model
    if body_fields and path_params:
        fields: Dict[str, Any] = {
            p.name: (op.param_types[p.name], ... if p.default is inspect.Parameter.empty else p.default)
            for p in body_fields
        }
        body_model = create_model(op.args_model.__name__.removesuffix('Args') + 'Body',
                                  __config__=ConfigDict(extra='forbid'), **fields)
    if body_fields:
        body_required = any(p.default is inspect.Parameter.empty for p in body_fields)
        params.append(inspect.Parameter('body', inspect.Parameter.KEYWORD_ONLY,
                                        default=Body(... if body_required else None),
                                        annotation=body_model if body_required else Optional[body_model]))

    async def endpoint(**received):
        body = received.pop('body', None)
        kwargs = dict(received)
        if body_fields:
            model = body if body is not None else body_model()
            kwargs.update({p.name: getattr(model, p.name) for p in body_fields})
        return await _run(executor, handle, op, kwargs)

    endpoint.__signature__ = inspect.Signature(params)
    endpoint.__name__ = f"{handle.name}_{op.name}"
    endpoint.__doc__ = op.func.__doc__
    return endpoint


def describe_module(handle: ModuleHandle) -> Dict[str, Any]:
    cls = handle.cls
    operations = []
    for op in sorted(cls.operations().values(), key=lambda o: o.name):
        operations.append({
            'name': op.name,
            'kind': op.kind,
            'id': op.id if op.kind == 'action' else None,
            'method': op.spec.method,
            'path': op.path(handle.is_core),
        })
    return {
        'name': handle.name,
        'kind': 'core' if handle.is_core else 'plugin',
        'interface_version': cls.interface_version,
        'operations': operations,
        'events': {name: {'topic': f"{handle.name}.{name}", 'schema': spec.model.model_json_schema()}
                   for name, spec in sorted(cls.events().items())},
        'extension_points': sorted(cls.extension_point_specs()),
    }


def build_router(manager: ModuleManager, executor) -> APIRouter:
    router = APIRouter()

    @router.get('/api/v1/modules', tags=['modules'])
    async def list_modules():
        return {
            'modules': [describe_module(handle) for handle in manager.handles()],
            'failed': manager.failed,
        }

    @router.get('/api/v1/actions', tags=['modules'])
    async def list_actions():
        return manager.catalog.describe()

    add_settings_routes(router, manager, executor)

    for handle in manager.handles():
        for op in sorted(handle.cls.operations().values(), key=lambda o: o.name):
            path = op.path(handle.is_core)
            response_model = None if op.returns_nothing else op.return_type
            router.add_api_route(
                path,
                _endpoint(executor, handle, op),
                methods=[op.spec.method],
                status_code=op.spec.status_code or (204 if op.returns_nothing else 200),
                response_model=response_model,
                response_class=Response if op.returns_nothing else JSONResponse,
                tags=[handle.name],
                summary=(op.func.__doc__ or '').strip().split('\n', 1)[0] or None,
                name=f"{handle.name}.{op.name}",
            )
        handle.instance.extra_routes(router)
    return router


def _blocking(executor):
    async def blocking(func, *args):
        try:
            return await asyncio.get_running_loop().run_in_executor(executor, func, *args)
        except OperationError as error:
            return _error(error.status, error.code, error.message)
    return blocking


def add_settings_routes(router: APIRouter, manager: ModuleManager, executor) -> None:
    """Settings of the modules and whether a restart is pending."""
    blocking = _blocking(executor)

    @router.get('/api/v1/settings/modules', tags=['settings'])
    async def list_module_settings():
        """Settings of every running module that has some: schema and current values."""
        return await blocking(manager.settings.list)

    @router.get('/api/v1/settings/modules/{name}', tags=['settings'])
    async def get_module_settings(name: str):
        return await blocking(manager.settings.describe, name)

    @router.put('/api/v1/settings/modules/{name}', tags=['settings'])
    async def update_module_settings(name: str, body: SettingsUpdate):
        """Change settings (only the given ones); they are saved to the config file right away."""
        return await blocking(manager.settings.update, name, body.values)

    @router.get('/api/v1/settings/restart', tags=['settings'])
    async def restart_state():
        """Whether changed settings or plugins only take effect after a restart."""
        return {'required': bool(manager.settings.restart_required),
                'modules': sorted(manager.settings.restart_required)}

    add_plugin_routes(router, manager, blocking)


def add_plugin_routes(router: APIRouter, manager: ModuleManager, blocking) -> None:
    """Installed plugins: list, enable or disable, install missing extras."""
    store = manager.settings

    def describe(name: str):
        return next(entry for entry in plugins.describe(store.cfg, manager, store.installer) if entry['name'] == name)

    def check_installed(name: str):
        if name not in plugins.installed():
            raise OperationError(404, 'unknown_plugin', f"Plugin '{name}' is not installed")

    @router.get('/api/v1/plugins', tags=['settings'])
    async def list_plugins():
        """Installed plugins, whether they are enabled and running, and what is missing."""
        return await blocking(plugins.describe, store.cfg, manager, store.installer)

    @router.put('/api/v1/plugins/{name}', tags=['settings'])
    async def enable_plugin(name: str, body: PluginState):
        """Enable or disable an installed plugin; takes effect after a restart."""
        def change():
            if body.enabled:
                check_installed(name)
            if plugins.set_enabled(store.cfg, name, body.enabled):
                store.save()
                store.restart_required.add(name)
            return describe(name)
        return await blocking(change)

    @router.post('/api/v1/plugins/{name}/extras', tags=['settings'], status_code=202)
    async def install_extras(name: str):
        """Install the packages a plugin is missing, in the background (see ``installing`` in the list)."""
        def start():
            check_installed(name)
            if not store.installer.start(name):
                raise OperationError(409, 'nothing_to_install',
                                     f"Nothing to install for '{name}', or another installation is running")
            return describe(name)
        return await blocking(start)
