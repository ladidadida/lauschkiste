"""Discovers, orders, starts and stops core modules and enabled plugins."""

import logging
import threading
from importlib.metadata import entry_points
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Type

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from lauschkiste.contract.catalog import ActionCatalog
from lauschkiste.contract.context import Context, ModuleConfig, ModulesView, strict_mode_default
from lauschkiste.contract.errors import ContractError
from lauschkiste.contract.module import CoreModule, Module, Plugin
from lauschkiste.contract.plugins import ENTRY_POINT_GROUP
from lauschkiste.contract.settings import SettingsStore
from lauschkiste.contract.version import CONTRACT_VERSION

logger = logging.getLogger('lauschkiste.contract')

def discover_plugins() -> Dict[str, Callable[[], type]]:
    """Installed plugins by entry-point name. Loading (importing) happens only when enabled."""
    return {ep.name: ep.load for ep in entry_points(group=ENTRY_POINT_GROUP)}


class ModuleHandle:
    """A started (or starting) module instance plus its lock and context."""

    def __init__(self, cls: Type[Module], instance: Module):
        self.cls = cls
        self.instance = instance
        self.name = cls.name
        self.lock = threading.RLock() if cls.concurrency == 'serialized' else None
        self.context: Optional[Context] = None
        self.started = False

    @property
    def is_core(self) -> bool:
        return self.cls.is_core

    def invoke(self, op_name: str, *args, **kwargs):
        op = self.cls.operations()[op_name]
        bound = getattr(self.instance, op.attr)
        if self.lock is None or not op.spec.exclusive:
            return bound(*args, **kwargs)
        with self.lock:
            return bound(*args, **kwargs)


class ModuleManager:
    def __init__(self, core_modules: Sequence[Type[CoreModule]], cfg, bus, *,
                 plugins: Optional[Dict[str, Callable[[], type]]] = None, strict: Optional[bool] = None):
        """
        :param core_modules: core module classes (order doesn't matter, ``requires`` decides)
        :param cfg: the main config handler; plugins are enabled under its ``plugins`` key
        :param bus: the event bus
        :param plugins: installed plugins by name (default: entry points of ``lauschkiste.plugins``)
        :param strict: raise instead of log on invalid events (default: ``$LAUSCHKISTE_STRICT``)
        """
        self._core_classes = list(core_modules)
        self._cfg = cfg
        self._bus = bus
        self._available_plugins = plugins
        self._strict = strict_mode_default() if strict is None else strict
        self.catalog = ActionCatalog()
        self._handles: Dict[str, ModuleHandle] = {}
        self._order: List[str] = []
        self.failed: Dict[str, str] = {}
        self.settings = SettingsStore(self, cfg)

    # -- loading --------------------------------------------------------------------------------

    def _enabled_plugin_names(self) -> List[str]:
        enabled = self._cfg.getn('plugins', default=None) or {}
        if isinstance(enabled, list):
            return [str(name) for name in enabled]
        if isinstance(enabled, dict):
            return [str(name) for name in enabled]
        raise ContractError("Config 'plugins' must be a mapping of plugin name to its settings")

    def _load_plugin_classes(self) -> List[Type[Plugin]]:
        names = self._enabled_plugin_names()
        if not names:
            return []
        available = self._available_plugins if self._available_plugins is not None else discover_plugins()
        classes = []
        for name in names:
            if name not in available:
                self._fail(name, f"enabled in config but not installed (available: {sorted(available) or 'none'})")
                continue
            try:
                cls = available[name]()
            except Exception as error:
                logger.exception(f"Plugin '{name}' failed to import")
                self._fail(name, f"import failed: {error.__class__.__name__}: {error}")
                continue
            if not (isinstance(cls, type) and issubclass(cls, Plugin)):
                self._fail(name, f"entry point does not point to a Plugin subclass: {cls!r}")
                continue
            if getattr(cls, 'name', None) != name:
                self._fail(name, f"entry point name differs from the plugin's name {getattr(cls, 'name', None)!r}")
                continue
            try:
                cls.validate_declaration()
            except ContractError as error:
                self._fail(name, str(error))
                continue
            if Version(CONTRACT_VERSION) not in SpecifierSet(cls.contract):
                self._fail(name, f"targets contract {cls.contract}, this core provides {CONTRACT_VERSION}")
                continue
            classes.append(cls)
        return classes

    def _fail(self, name: str, reason: str) -> None:
        self.failed[name] = reason
        logger.error(f"Plugin '{name}' skipped: {reason}")

    def _sort(self, classes: List[Type[Module]]) -> List[Type[Module]]:
        by_name: Dict[str, Type[Module]] = {}
        for cls in classes:
            if cls.name in by_name:
                raise ContractError(f"Two modules are named '{cls.name}'")
            by_name[cls.name] = cls

        ordered: List[Type[Module]] = []
        state: Dict[str, str] = {}

        def visit(cls: Type[Module], path: List[str]):
            mark = state.get(cls.name)
            if mark == 'done':
                return
            if mark == 'visiting':
                cycle = ' -> '.join(path[path.index(cls.name):] + [cls.name])
                raise ContractError(f"Dependency cycle: {cycle}")
            state[cls.name] = 'visiting'
            for dep in cls.required_modules():
                if dep in by_name:
                    visit(by_name[dep], path + [cls.name])
            state[cls.name] = 'done'
            ordered.append(cls)

        for cls in classes:
            visit(cls, [])
        return ordered

    def _check_requirements(self, cls: Type[Module], present: Dict[str, Type[Module]]) -> Optional[str]:
        for dep, spec in cls.required_modules().items():
            if dep in self.failed:
                return f"requires '{dep}', which was skipped"
            target = present.get(dep)
            if target is None:
                return f"requires '{dep}', which is not available"
            if cls.is_core and not target.is_core:
                raise ContractError(f"Core module '{cls.name}' must not require plugin '{dep}'")
            if spec is not None and Version(target.interface_version) not in SpecifierSet(spec):
                return f"requires '{dep}' {spec}, available is {target.interface_version}"
        return None

    def load(self) -> None:
        for cls in self._core_classes:
            if not (isinstance(cls, type) and issubclass(cls, CoreModule)):
                raise ContractError(f"{cls!r} is not a CoreModule")
            cls.validate_declaration()
        classes: List[Type[Module]] = [*self._core_classes, *self._load_plugin_classes()]
        ordered = self._sort(classes)
        present = {cls.name: cls for cls in ordered}
        for cls in ordered:
            problem = self._check_requirements(cls, present)
            if problem is not None:
                if cls.is_core:
                    raise ContractError(f"Core module '{cls.name}' {problem}")
                self._fail(cls.name, problem)
                present.pop(cls.name)
                continue
            self._order.append(cls.name)
            self._handles[cls.name] = ModuleHandle(cls, cls())

    # -- lifecycle ------------------------------------------------------------------------------

    def _context(self, handle: ModuleHandle) -> Context:
        prefix = (handle.name,) if handle.is_core else ('plugins', handle.name)
        allowed = {dep: self._handles[dep] for dep in handle.cls.required_modules() if dep in self._handles}
        return Context(handle, bus=self._bus, config=ModuleConfig(self._cfg, prefix),
                       modules=ModulesView(handle.name, allowed), actions=self.catalog, strict=self._strict)

    def start(self) -> None:
        for name in list(self._order):
            handle = self._handles[name]
            problem = next((f"requires '{dep}', which failed to start"
                            for dep in handle.cls.required_modules() if dep in self.failed), None)
            if problem is not None:
                self._drop(name, problem)
                continue
            handle.context = self._context(handle)
            logger.info(f"Starting {'core module' if handle.is_core else 'plugin'} '{name}'")
            try:
                handle.instance.start(handle.context)
            except Exception as error:
                handle.context.close()
                if handle.is_core:
                    raise
                logger.exception(f"Plugin '{name}' failed to start")
                self._drop(name, f"start failed: {error.__class__.__name__}: {error}")
                continue
            handle.started = True
            self.catalog.add_module(handle)

    def ready(self) -> None:
        for handle in list(self.handles()):
            try:
                handle.instance.ready()
            except Exception as error:
                if handle.is_core:
                    raise
                logger.exception(f"Plugin '{handle.name}' failed in ready()")
                self.catalog.remove_module(handle.name)
                handle.started = False
                if handle.context is not None:
                    handle.context.close()
                self._drop(handle.name, f"ready failed: {error.__class__.__name__}: {error}")

    def _drop(self, name: str, reason: str) -> None:
        self._fail(name, reason)
        self._order.remove(name)
        self._handles.pop(name, None)

    def stop(self) -> List[threading.Thread]:
        threads: List[threading.Thread] = []
        for name in reversed(self._order):
            handle = self._handles[name]
            if not handle.started:
                continue
            self.catalog.remove_module(name)
            try:
                threads.extend(t for t in (handle.instance.stop() or []) if t is not None)
            except Exception:
                logger.exception(f"Module '{name}' failed to stop")
            finally:
                handle.started = False
                if handle.context is not None:
                    handle.context.close()
        return threads

    # -- access ---------------------------------------------------------------------------------

    def handles(self) -> Iterable[ModuleHandle]:
        return [self._handles[name] for name in self._order if self._handles[name].started]

    def handle(self, name: str) -> ModuleHandle:
        try:
            handle = self._handles[name]
        except KeyError:
            raise KeyError(f"Module '{name}' is not loaded") from None
        return handle

    def instance(self, name: str) -> Any:
        return self.handle(name).instance

    def __contains__(self, name: str) -> bool:
        return name in self._handles and self._handles[name].started
