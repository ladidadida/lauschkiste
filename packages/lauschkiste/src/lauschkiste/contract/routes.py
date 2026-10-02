"""FastAPI routes generated from module operations, plus ``GET /api/v1/modules``."""

import asyncio
import inspect
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Path, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from pydantic import ConfigDict, create_model

from lauschkiste.contract.declarations import Operation
from lauschkiste.contract.errors import ActionError, OperationError
from lauschkiste.contract.manager import ModuleHandle, ModuleManager

logger = logging.getLogger('lauschkiste.contract.routes')


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
