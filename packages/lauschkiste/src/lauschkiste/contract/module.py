"""Base classes for core modules and plugins."""

import re
import threading
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Dict, List, Mapping, Optional, Tuple, Type, Union

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version
from pydantic import BaseModel

from lauschkiste.contract.declarations import EventSpec, ExtensionPointSpec, Operation, operation_spec
from lauschkiste.contract.errors import ContractError
from lauschkiste.contract.version import CONTRACT_VERSION

if TYPE_CHECKING:
    from lauschkiste.contract.context import Context

_NAME_RE = re.compile(r'^[a-z][a-z0-9_]*$')

Requires = Union[Tuple[str, ...], Mapping[str, str]]


class Module:
    """Common base of :class:`CoreModule` and :class:`Plugin`. Not subclassed directly."""

    name: ClassVar[str]
    interface_version: ClassVar[str] = '1.0'
    requires: ClassVar[Requires] = ()
    #: 'serialized': every operation runs under a per-module lock. 'threadsafe': no lock.
    concurrency: ClassVar[str] = 'serialized'
    is_core: ClassVar[bool] = False
    #: The settings of the module's config section, editable through the web app. Field titles and
    #: descriptions are shown; ``Field(json_schema_extra={'widget': 'action'})`` marks an action entry.
    settings: ClassVar[Optional[Type[BaseModel]]] = None

    def start(self, ctx: 'Context') -> None:
        pass

    def ready(self) -> None:
        """Called once every module has started, in start order. All actions are available now."""

    def stop(self) -> List[threading.Thread]:
        return []

    # A module keeping its settings outside its section of the main config defines
    # ``settings_storage(self) -> (config handler, key path)``.

    def settings_changed(self, changed: Dict[str, Any]) -> bool:
        """Settings were changed through the web app (already in ``ctx.config``). Return True if
        they take effect right away, False if Lauschkiste must restart for them."""
        return False

    def extra_routes(self, router) -> None:
        """Escape hatch for routes the declarations can't express (e.g. streaming uploads).

        Receives a FastAPI ``APIRouter``; paths should live under ``/api/v1/<name>``."""

    # -- introspection --------------------------------------------------------------------------

    @classmethod
    def validate_declaration(cls) -> None:
        if cls in (Module, CoreModule, Plugin):
            raise ContractError(f"{cls.__name__} can't be used as a module itself")
        name = getattr(cls, 'name', None)
        if not isinstance(name, str) or not _NAME_RE.match(name):
            raise ContractError(f"{cls.__qualname__}: 'name' must match {_NAME_RE.pattern}, got {name!r}")
        try:
            Version(cls.interface_version)
        except InvalidVersion as error:
            raise ContractError(f"{name}: invalid interface_version {cls.interface_version!r}") from error
        if cls.concurrency not in ('serialized', 'threadsafe'):
            raise ContractError(f"{name}: concurrency must be 'serialized' or 'threadsafe'")
        for dep, spec in cls.required_modules().items():
            if spec is not None:
                try:
                    SpecifierSet(spec)
                except InvalidSpecifier as error:
                    raise ContractError(f"{name}: invalid version specifier for '{dep}': {spec!r}") from error
        cls.operations()
        cls.events()

    @classmethod
    def required_modules(cls) -> Dict[str, Union[str, None]]:
        if isinstance(cls.requires, Mapping):
            return dict(cls.requires)
        return {dep: None for dep in cls.requires}

    @classmethod
    def operations(cls) -> Dict[str, Operation]:
        cache = cls.__dict__.get('_lauschkiste_operations')
        if cache is not None:
            return cache
        ops = {}
        for attr in dir(cls):
            func = getattr(cls, attr, None)
            spec = operation_spec(func) if callable(func) else None
            if spec is not None and callable(func):
                op = Operation(cls.name, attr, func, spec)
                if op.name in ops:
                    raise ContractError(f"{cls.name}: two operations are named '{op.name}'")
                ops[op.name] = op
        cls._lauschkiste_operations = ops
        return ops

    @classmethod
    def events(cls) -> Dict[str, EventSpec]:
        found = {}
        for attr in dir(cls):
            value = getattr(cls, attr, None)
            if isinstance(value, EventSpec):
                if value.name in found and found[value.name] is not value:
                    raise ContractError(f"{cls.name}: event '{value.name}' declared twice")
                found[value.name] = value
        return found

    @classmethod
    def extension_point_specs(cls) -> Dict[str, ExtensionPointSpec]:
        found = {}
        for klass in reversed(cls.__mro__):
            for value in vars(klass).values():
                if isinstance(value, ExtensionPointSpec):
                    found[value.name] = value
        return found


class CoreModule(Module):
    """Always shipped, always running part of Lauschkiste."""

    is_core = True


class Plugin(Module):
    """Separately installed, opt-in module. Declares which framework contract it targets."""

    contract: ClassVar[str] = f">={Version(CONTRACT_VERSION).major}.0,<{Version(CONTRACT_VERSION).major + 1}"
    #: Extras of the plugin's own package it needs (installed by `lauschctl plugin enable --with-extras`)
    extras: ClassVar[Tuple[str, ...]] = ()
    #: Capabilities it offers other plugins, e.g. ``('board', 'gpio', 'i2c')``; only one plugin may provide 'board'
    provides: ClassVar[Tuple[str, ...]] = ()
    #: Capabilities an enabled plugin must provide, e.g. ``('i2c',)``
    needs: ClassVar[Tuple[str, ...]] = ()

    @classmethod
    def detect(cls, read: Callable[[str], Optional[str]]) -> Optional[str]:
        """The hardware of this plugin found on this machine (e.g. a board model), or None.

        ``read(path)`` returns a file's text or None."""
        return None

    @classmethod
    def validate_declaration(cls) -> None:
        super().validate_declaration()
        try:
            SpecifierSet(cls.contract)
        except InvalidSpecifier as error:
            raise ContractError(f"{cls.name}: invalid contract specifier {cls.contract!r}") from error
