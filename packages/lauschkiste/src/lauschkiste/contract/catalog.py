"""Card-triggerable actions of all started modules, addressed by ``<module>.<action>``."""

import logging
import threading
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from pydantic import ValidationError

from lauschkiste.contract.declarations import Operation
from lauschkiste.contract.errors import ActionError

if TYPE_CHECKING:
    from lauschkiste.contract.manager import ModuleHandle

logger = logging.getLogger('lauschkiste.contract.actions')


class ActionCatalog:
    def __init__(self):
        self._lock = threading.Lock()
        self._actions: Dict[str, Tuple['ModuleHandle', Operation]] = {}

    def add_module(self, handle: 'ModuleHandle') -> None:
        with self._lock:
            for op in handle.cls.operations().values():
                if op.kind == 'action':
                    self._actions[op.id] = (handle, op)

    def remove_module(self, name: str) -> None:
        with self._lock:
            for action_id in [a for a, (h, _) in self._actions.items() if h.name == name]:
                del self._actions[action_id]

    def ids(self) -> List[str]:
        with self._lock:
            return sorted(self._actions)

    def __contains__(self, action_id: str) -> bool:
        with self._lock:
            return action_id in self._actions

    def operation(self, action_id: str) -> Operation:
        return self._lookup(action_id)[1]

    def _lookup(self, action_id: str):
        with self._lock:
            try:
                return self._actions[action_id]
            except KeyError:
                raise ActionError(f"Unknown action '{action_id}'") from None

    def validate(self, action_id: str, args: Optional[dict] = None) -> Dict[str, Any]:
        """Check that ``action_id`` exists and ``args`` fit its signature. Returns coerced args."""
        _, op = self._lookup(action_id)
        if args is not None and not isinstance(args, dict):
            raise ActionError(f"Arguments for '{action_id}' must be a mapping, got {type(args).__name__}")
        try:
            return op.validate_args(args)
        except ValidationError as error:
            details = '; '.join(
                f"{'.'.join(str(p) for p in e['loc']) or 'args'}: {e['msg']}" for e in error.errors())
            raise ActionError(f"Invalid arguments for '{action_id}': {details}") from None

    def call(self, action_id: str, args: Optional[dict] = None) -> Any:
        handle, op = self._lookup(action_id)
        kwargs = self.validate(action_id, args)
        return handle.invoke(op.name, **kwargs)

    def call_ignore_errors(self, action_id: str, args: Optional[dict] = None) -> Any:
        try:
            return self.call(action_id, args)
        except Exception as error:
            logger.error(f"Action '{action_id}' with args {args} failed: {error.__class__.__name__}: {error}",
                         exc_info=not isinstance(error, ActionError))
            return None

    def describe(self) -> List[Dict[str, Any]]:
        with self._lock:
            items = list(self._actions.items())
        return [
            {
                'id': action_id,
                'description': (op.func.__doc__ or '').strip().split('\n\n', 1)[0],
                'args': op.args_model.model_json_schema(),
            }
            for action_id, (_, op) in sorted(items)
        ]
