"""Declarations a module uses to describe its interface: operations, events, extension points."""

import inspect
import threading
import typing
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Type

from pydantic import BaseModel, ConfigDict, create_model

from lauschkiste.contract.errors import ContractError

_OPERATION_ATTR = '__jukebox_operation__'


@dataclass(frozen=True)
class OperationSpec:
    kind: str  # 'action' | 'query'
    method: str
    path: Optional[str]
    exclusive: bool
    name: Optional[str] = None
    status_code: Optional[int] = None


def _decorate(func, spec: OperationSpec):
    setattr(func, _OPERATION_ATTR, spec)
    return func


def action(func: Optional[Callable] = None, *, method: str = 'POST', path: Optional[str] = None,
           exclusive: bool = True, name: Optional[str] = None, status_code: Optional[int] = None):
    """Declare a state-changing operation: REST route, card action and in-process call.

    ``name`` overrides the operation name (default: the method name), e.g. where the method name
    would clash with the lifecycle methods ``start``/``stop``/``ready``. ``status_code`` replaces
    the default HTTP status of a successful call (200, or 204 without a result)."""
    method = method.upper()
    if method not in ('POST', 'PUT', 'DELETE'):
        raise ContractError(f"@action method must be POST, PUT or DELETE, not '{method}'")
    spec = OperationSpec('action', method, path, exclusive, name, status_code)
    if func is not None:
        return _decorate(func, spec)
    return lambda f: _decorate(f, spec)


def query(func: Optional[Callable] = None, *, path: Optional[str] = None, exclusive: bool = True,
          name: Optional[str] = None):
    """Declare a read-only operation: GET route and in-process call, not card-triggerable."""
    spec = OperationSpec('query', 'GET', path, exclusive, name)
    if func is not None:
        return _decorate(func, spec)
    return lambda f: _decorate(f, spec)


def operation_spec(func) -> Optional[OperationSpec]:
    return getattr(func, _OPERATION_ATTR, None)


class EventSpec:
    """A declared event. Published through ``ctx.publish(spec, payload)`` as ``<module>.<name>``."""

    def __init__(self, name: str, model: Type[BaseModel]):
        if not name or '.' in name:
            raise ContractError(f"Invalid event name '{name}'")
        if not (isinstance(model, type) and issubclass(model, BaseModel)):
            raise ContractError(f"Event '{name}' needs a pydantic model, got {model!r}")
        self.name = name
        self.model = model

    def __repr__(self):
        return f"event({self.name!r}, {self.model.__name__})"


def event(name: str, model: Type[BaseModel]) -> EventSpec:
    return EventSpec(name, model)


class ExtensionPoint:
    """Named implementations of a protocol, registered by other modules."""

    def __init__(self, name: str, protocol: type):
        self.name = name
        self.protocol = protocol
        self._lock = threading.Lock()
        self._items: Dict[str, Any] = {}
        self._listeners: List[Callable[[str, Any], None]] = []

    def on_register(self, listener: Callable[[str, Any], None]) -> None:
        """Call ``listener(key, implementation)`` for every current and future registration."""
        with self._lock:
            self._listeners.append(listener)
            current = list(self._items.items())
        for key, implementation in current:
            listener(key, implementation)

    def register(self, key: str, implementation: Any) -> None:
        missing = [m for m in protocol_methods(self.protocol)
                   if not callable(getattr(implementation, m, None))]
        if missing:
            raise ContractError(
                f"'{key}' does not implement {self.protocol.__name__} for extension point "
                f"'{self.name}': missing {missing}")
        with self._lock:
            if key in self._items:
                raise ContractError(f"'{key}' is already registered at extension point '{self.name}'")
            self._items[key] = implementation
            listeners = list(self._listeners)
        for listener in listeners:
            listener(key, implementation)

    def unregister(self, key: str) -> None:
        with self._lock:
            self._items.pop(key, None)

    def get(self, key: str) -> Any:
        with self._lock:
            try:
                return self._items[key]
            except KeyError:
                available = ', '.join(self._items) or 'none'
                raise KeyError(f"Nothing registered as '{key}' at '{self.name}'. Available: {available}") from None

    def items(self):
        with self._lock:
            return list(self._items.items())

    def names(self):
        with self._lock:
            return list(self._items)

    def __contains__(self, key):
        with self._lock:
            return key in self._items


class ExtensionPointSpec:
    """Class-level declaration of an extension point; each module instance gets its own registry."""

    def __init__(self, name: str, protocol: type):
        self.name = name
        self.protocol = protocol
        self._attr = None

    def __set_name__(self, owner, attr):
        self._attr = attr

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        store = instance.__dict__.setdefault('_jukebox_extension_points', {})
        if self.name not in store:
            store[self.name] = ExtensionPoint(self.name, self.protocol)
        return store[self.name]


def extension_point(name: str, protocol: type) -> ExtensionPointSpec:
    return ExtensionPointSpec(name, protocol)


def protocol_methods(protocol: type):
    return sorted(
        name for name, value in vars(protocol).items()
        if not name.startswith('_') and callable(value)
    )


class Operation:
    """An operation of a module class with its argument model and return type."""

    def __init__(self, module_name: str, attr: str, func: Callable, spec: OperationSpec):
        self.module_name = module_name
        self.attr = attr
        self.name = spec.name or attr
        if not self.name.isidentifier():
            raise ContractError(f"{module_name}.{attr}: invalid operation name {self.name!r}")
        self.func = func
        self.spec = spec
        self.signature = inspect.signature(func)
        try:
            hints = typing.get_type_hints(func, include_extras=True)
        except Exception as error:
            raise ContractError(f"{module_name}.{attr}: cannot resolve type hints ({error})") from error
        self.params = [p for p in self.signature.parameters.values() if p.name != 'self']
        for param in self.params:
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                raise ContractError(f"{module_name}.{attr}: *args/**kwargs are not allowed in operations")
            if param.name not in hints:
                raise ContractError(f"{module_name}.{attr}: parameter '{param.name}' needs a type annotation")
        if 'return' not in hints:
            raise ContractError(f"{module_name}.{attr}: needs a return type annotation")
        self.param_types = {p.name: hints[p.name] for p in self.params}
        self.return_type = hints['return']
        fields: Dict[str, Any] = {
            p.name: (hints[p.name], ... if p.default is inspect.Parameter.empty else p.default)
            for p in self.params
        }
        model_name = ''.join(part.capitalize() for part in f"{module_name}_{self.name}".split('_')) + 'Args'
        self.args_model = create_model(model_name, __config__=ConfigDict(extra='forbid'), **fields)

    @property
    def kind(self):
        return self.spec.kind

    @property
    def id(self):
        return f"{self.module_name}.{self.name}"

    @property
    def returns_nothing(self):
        return self.return_type is type(None)

    def path(self, is_core: bool) -> str:
        path = self.spec.path
        if path is None:
            return f"/api/v1/{self.module_name}/{self.name}"
        if path.startswith('/api/'):
            if not is_core:
                raise ContractError(f"{self.id}: only core modules may declare absolute paths")
            return path
        if not path.startswith('/'):
            path = '/' + path
        return f"/api/v1/{self.module_name}{path.rstrip('/')}"

    def path_params(self, is_core: bool):
        path = self.path(is_core)
        return [p.name for p in self.params if '{' + p.name + '}' in path]

    def validate_args(self, args: Optional[dict]) -> dict:
        """Validate a mapping of arguments; return the coerced keyword arguments."""
        instance = self.args_model.model_validate(args or {})
        return {p.name: getattr(instance, p.name) for p in self.params}
