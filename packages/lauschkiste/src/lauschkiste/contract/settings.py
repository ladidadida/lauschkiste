"""Module settings: read, validate and store a module's config section through its ``settings`` model."""

import logging
from typing import Any, Dict, List, Set

from pydantic import BaseModel, ConfigDict, ValidationError

from lauschkiste.contract.errors import OperationError

logger = logging.getLogger('lauschkiste.contract.settings')


class ActionEntry(BaseModel):
    """An action with its arguments, as on cards (shown as an action picker in the web app)."""
    model_config = ConfigDict(json_schema_extra={'widget': 'action'})

    action: str
    args: Dict[str, Any] = {}


def config_prefix(handle) -> tuple:
    return (handle.name,) if handle.is_core else ('plugins', handle.name)


def current_values(model: type, section: Any) -> Dict[str, Any]:
    """The settings from a config section; invalid or unknown entries fall back to the defaults."""
    data = {key: value for key, value in (section or {}).items() if key in model.model_fields} \
        if isinstance(section, dict) else {}
    while True:
        try:
            return model.model_validate(data).model_dump(mode='json')
        except ValidationError as error:
            invalid = {str(entry['loc'][0]) for entry in error.errors() if entry.get('loc')}
            if not invalid & set(data):
                return model().model_dump(mode='json')
            for key in invalid:
                logger.warning(f"Ignoring invalid setting '{key}': {data.pop(key, None)!r}")


def _message(error: ValidationError) -> str:
    return '; '.join(f"{'.'.join(str(part) for part in entry['loc'])}: {entry['msg']}" for entry in error.errors())


class SettingsStore:
    """Settings of the started modules, written to the main config file right away."""

    def __init__(self, manager, cfg):
        self._manager = manager
        self.cfg = cfg
        self.restart_required: Set[str] = set()

    def _handle(self, name: str):
        if name not in self._manager:
            raise OperationError(404, 'unknown_module', f"Module '{name}' is not running")
        handle = self._manager.handle(name)
        if handle.cls.settings is None:
            raise OperationError(404, 'no_settings', f"Module '{name}' has no settings")
        return handle

    def describe(self, name: str) -> Dict[str, Any]:
        handle = self._handle(name)
        model = handle.cls.settings
        section = self.cfg.getn(*config_prefix(handle), default=None)
        return {
            'name': name,
            'kind': 'core' if handle.is_core else 'plugin',
            'title': (handle.cls.__doc__ or '').strip().split('\n', 1)[0] or name,
            'schema': model.model_json_schema(),
            'values': current_values(model, section),
            'restart_required': name in self.restart_required,
        }

    def list(self) -> List[Dict[str, Any]]:
        return [self.describe(handle.name) for handle in self._manager.handles() if handle.cls.settings is not None]

    def update(self, name: str, values: Dict[str, Any]) -> Dict[str, Any]:
        handle = self._handle(name)
        model = handle.cls.settings
        unknown = sorted(set(values) - set(model.model_fields))
        if unknown:
            raise OperationError(422, 'unknown_setting', f"Unknown settings for '{name}': {', '.join(unknown)}")
        prefix = config_prefix(handle)
        merged = {**current_values(model, self.cfg.getn(*prefix, default=None)), **values}
        try:
            validated = model.model_validate(merged).model_dump(mode='json')
        except ValidationError as error:
            raise OperationError(422, 'invalid_setting', _message(error)) from None
        changed = {key: validated[key] for key in values}
        with self.cfg:
            for key, value in changed.items():
                if value is None:
                    section = self.cfg.getn(*prefix, default=None)
                    if isinstance(section, dict):
                        section.pop(key, None)
                else:
                    self.cfg.setn(*prefix, key, value=value)
        self.save()
        try:
            applied = bool(handle.instance.settings_changed(changed))
        except Exception:
            logger.exception(f"Module '{name}' failed to apply its changed settings")
            applied = False
        if not applied:
            self.restart_required.add(name)
        return self.describe(name)

    def save(self) -> None:
        if getattr(self.cfg, 'loaded_from', None):
            self.cfg.save(only_if_changed=False)

