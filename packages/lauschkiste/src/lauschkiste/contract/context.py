"""What a module sees of the rest of the system."""

import contextlib
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, ValidationError

import lauschkiste.paths
from lauschkiste.contract.declarations import EventSpec, ExtensionPointSpec
from lauschkiste.contract.errors import ContractError

if TYPE_CHECKING:
    from lauschkiste.contract.catalog import ActionCatalog
    from lauschkiste.contract.manager import ModuleHandle

logger = logging.getLogger('jb.contract')


def strict_mode_default() -> bool:
    return (lauschkiste.paths.getenv('STRICT') or '').lower() in ('1', 'true', 'yes')


class ModuleConfig:
    """A module's own section of the main config (``<name>`` for core, ``plugins.<name>`` for plugins)."""

    def __init__(self, cfg, prefix: Tuple[str, ...]):
        self._cfg = cfg
        self._prefix = prefix

    def get(self, *keys, default=None):
        return self._cfg.getn(*self._prefix, *keys, default=default)

    def setdefault(self, *keys, value):
        return self._cfg.setndefault(*self._prefix, *keys, value=value)

    def set(self, *keys, value) -> None:
        self._cfg.setn(*self._prefix, *keys, value=value)

    def __getitem__(self, key):
        value = self.get(key, default=KeyError)
        if value is KeyError:
            raise KeyError(key)
        return value

    def __contains__(self, key):
        return self.get(key, default=KeyError) is not KeyError

    def as_dict(self) -> Dict[str, Any]:
        value = self._cfg.getn(*self._prefix, default=None)
        return dict(value) if isinstance(value, dict) else {}


class ModuleProxy:
    """The contract surface of another module: its operations and extension points."""

    def __init__(self, handle: 'ModuleHandle'):
        self._handle = handle

    def __getattr__(self, attr):
        handle = self._handle
        if attr in handle.cls.operations():
            return lambda *args, **kwargs: handle.invoke(attr, *args, **kwargs)
        if isinstance(getattr(handle.cls, attr, None), ExtensionPointSpec):
            return getattr(handle.instance, attr)
        raise AttributeError(f"'{handle.name}' has no operation or extension point '{attr}'")

    def __repr__(self):
        return f"<module {self._handle.name}>"


class ModulesView:
    def __init__(self, owner: str, allowed: Dict[str, 'ModuleHandle']):
        self._owner = owner
        self._allowed = allowed

    def __getattr__(self, name):
        try:
            return ModuleProxy(self._allowed[name])
        except KeyError:
            raise ContractError(
                f"'{self._owner}' accesses module '{name}' without listing it in 'requires'") from None

    def __getitem__(self, name):
        return self.__getattr__(name)


class Context:
    def __init__(self, handle: 'ModuleHandle', *, bus, config: ModuleConfig, modules: ModulesView,
                 actions: 'ActionCatalog', strict: bool):
        self._handle = handle
        self._bus = bus
        self._strict = strict
        self._subscriptions: List[Callable] = []
        self._executors: List[ThreadPoolExecutor] = []
        self._lock = threading.Lock()
        self.config = config
        self.modules = modules
        self.actions = actions
        self.logger = logging.getLogger(f'jb.{handle.name}')

    @property
    def name(self) -> str:
        return self._handle.name

    @property
    def lock(self):
        """The module's own lock, for work outside operations (e.g. background threads).

        A no-op context manager for ``concurrency = 'threadsafe'`` modules."""
        return self._handle.lock if self._handle.lock is not None else contextlib.nullcontext()

    def _own_event(self, spec: EventSpec) -> EventSpec:
        declared = self._handle.cls.events().get(getattr(spec, 'name', ''))
        if declared is not spec:
            raise ContractError(f"'{self.name}' publishes an event it did not declare: {spec!r}")
        return spec

    def topic(self, spec: EventSpec) -> str:
        return f"{self.name}.{spec.name}"

    def publish(self, spec: EventSpec, payload) -> None:
        spec = self._own_event(spec)
        try:
            if isinstance(payload, spec.model):
                model = spec.model.model_validate(payload.model_dump())
            elif isinstance(payload, BaseModel):
                raise TypeError(f"expected {spec.model.__name__}, got {type(payload).__name__}")
            else:
                model = spec.model.model_validate(payload)
        except (ValidationError, TypeError) as error:
            if self._strict:
                raise
            self.logger.error(f"Dropping invalid event '{self.topic(spec)}': {error}")
            return
        self._bus.publish(self.topic(spec), model.model_dump(mode='json'))

    def revoke(self, spec: EventSpec) -> None:
        self._bus.publish(self.topic(self._own_event(spec)), None)

    def subscribe(self, topic_prefix: str, callback: Callable[[str, Optional[Any]], None]) -> None:
        """Call ``callback(topic, payload)`` for every event under ``topic_prefix``; payload None = revoked."""
        def listener(topic, payload):
            if topic.startswith(topic_prefix):
                callback(topic, payload)
        with self._lock:
            self._subscriptions.append(listener)
        self._bus.register(listener)

    def executor(self, name: str, workers: int = 1) -> ThreadPoolExecutor:
        pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix=f'{self.name}.{name}')
        with self._lock:
            self._executors.append(pool)
        return pool

    def close(self) -> None:
        with self._lock:
            subscriptions, self._subscriptions = self._subscriptions, []
            executors, self._executors = self._executors, []
        for listener in subscriptions:
            self._bus.unregister(listener)
        for pool in executors:
            pool.shutdown(wait=False, cancel_futures=True)
