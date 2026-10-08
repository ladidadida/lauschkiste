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


def storage(handle, cfg) -> tuple:
    """(config handler, key path) of a module's settings: its section of the main config, unless the
    module keeps them elsewhere (``settings_storage()``)."""
    custom = getattr(handle.instance, 'settings_storage', None)
    if callable(custom):
        return custom()
    return cfg, ((handle.name,) if handle.is_core else ('plugins', handle.name))


def secret_fields(model: type) -> Set[str]:
    """Fields marked ``json_schema_extra={'secret': True}``: shown as password fields, never sent to the client."""
    return {name for name, field in model.model_fields.items()
            if isinstance(field.json_schema_extra, dict) and field.json_schema_extra.get('secret')}


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
        self.secrets = manager.secrets
        self.restart_required: Set[str] = set()
        from lauschkiste.contract.plugins import ExtrasInstaller
        self.installer = ExtrasInstaller(on_installed=self.restart_required.add)

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
        cfg, prefix = storage(handle, self.cfg)
        section = cfg.getn(*prefix, default=None)
        values = current_values(model, section)
        secrets = sorted(secret_fields(model))
        is_set = [key for key in secrets if self.secrets.get(*self._secret_prefix(handle), key)]
        for key in secrets:
            values[key] = ''
        return {
            'name': name,
            'kind': 'core' if handle.is_core else 'plugin',
            'title': (handle.cls.__doc__ or '').strip().split('\n', 1)[0] or name,
            'schema': model.model_json_schema(),
            'values': values,
            'secrets_set': is_set,
            'restart_required': name in self.restart_required,
        }

    def list(self) -> List[Dict[str, Any]]:
        return [self.describe(handle.name) for handle in self._manager.handles() if handle.cls.settings is not None]

    def update(self, name: str, values: Dict[str, Any]) -> Dict[str, Any]:
        handle = self._handle(name)
        model = handle.cls.settings
        values = {key: value for key, value in values.items()
                  if not (key in secret_fields(model) and value in ('', None))}
        unknown = sorted(set(values) - set(model.model_fields))
        if unknown:
            raise OperationError(422, 'unknown_setting', f"Unknown settings for '{name}': {', '.join(unknown)}")
        cfg, prefix = storage(handle, self.cfg)
        merged = {**current_values(model, cfg.getn(*prefix, default=None)), **values}
        try:
            validated = model.model_validate(merged).model_dump(mode='json')
        except ValidationError as error:
            raise OperationError(422, 'invalid_setting', _message(error)) from None
        changed = {key: validated[key] for key in values}
        secrets = secret_fields(model)
        for key in secrets & set(changed):
            self.secrets.set(*self._secret_prefix(handle), key, value=changed[key])
        with cfg:
            for key, value in changed.items():
                if key in secrets:
                    continue
                if value is None:
                    section = cfg.getn(*prefix, default=None)
                    if isinstance(section, dict):
                        section.pop(key, None)
                else:
                    cfg.setn(*prefix, key, value=value)
        self.save(cfg)
        try:
            applied = bool(handle.instance.settings_changed(changed))
        except Exception:
            logger.exception(f"Module '{name}' failed to apply its changed settings")
            applied = False
        if not applied:
            self.restart_required.add(name)
        return self.describe(name)

    @staticmethod
    def _secret_prefix(handle) -> tuple:
        return (handle.name,) if handle.is_core else ('plugins', handle.name)

    def save(self, cfg=None) -> None:
        cfg = cfg if cfg is not None else self.cfg
        if getattr(cfg, 'loaded_from', None):
            cfg.save(only_if_changed=False)

