"""What is attached to the device: peripheral plugins are proposed once the device is known, then their options."""

import typing
from typing import Any, Dict, List, Optional, Tuple

import lauschkiste.common.cfghandler
import lauschkiste.contract.plugins as plugins
from lauschkiste_cli import plugin
from lauschkiste_cli.setup.base import Context, Question, Step
from lauschkiste_cli.setup.steps import device, extra_plugins

KIND = 'peripheral'


def _label(name: str, cls) -> str:
    return getattr(cls, 'title', '') or plugins.readable(name)


def candidates(ctx: Context) -> Dict[str, type]:
    """The installed peripheral plugins that can work with the device."""
    device_class = device._device_classes().get(ctx.device_name() or '')
    found = {}
    for name, entry_point in sorted(plugins.installed().items()):
        cls, _ = plugins.load(entry_point)
        if cls is None or getattr(cls, 'setup_kind', '') != KIND:
            continue
        if plugins.blocker(cls, [device_class] if device_class is not None else []) is None:
            found[name] = cls
    return found


def installed_from_other_sources() -> List[str]:
    return [name for names in extra_plugins.all_installed().values() for name in names]


def chosen(ctx: Context) -> List[str]:
    """The candidates the user wants (the answers; the enabled ones where nothing was asked)."""
    enabled = ctx.enabled_plugins()
    return [name for name in candidates(ctx) if ctx.answer(f'peripheral_{name}', name in enabled)]


class PeripheralsStep(Step):
    name = 'peripherals'
    title = 'Attached hardware'
    phase = 'peripherals'

    def questions_for(self, ctx):
        enabled, extra = ctx.enabled_plugins(), installed_from_other_sources()
        return tuple(
            Question(f'peripheral_{name}', f"Use '{_label(name, cls)}'?", default=name in enabled or name in extra,
                     help=(getattr(cls, '__doc__', None) or '').strip().split('\n', 1)[0].replace('``', ''))
            for name, cls in candidates(ctx).items())

    def wanted(self, ctx):
        return bool(candidates(ctx))

    def check(self, ctx):
        enabled, wanted = ctx.enabled_plugins(), chosen(ctx)
        problems = [f"plugin '{name}' is not enabled" for name in wanted if name not in enabled]
        problems += [f"plugin '{name}' is enabled but not chosen" for name in candidates(ctx)
                     if name in enabled and name not in wanted]
        problems += [f"dependencies {req} are not installed" for name in wanted for req in plugin.missing_extras(name)]
        return problems

    def apply(self, ctx):
        wanted = chosen(ctx)
        for name in wanted:
            extras = plugin.missing_extras(name)
            if extras:
                plugin.install_requirements(plugin.plugin_extras(name))
        plugin.add_to_config(ctx.config_path, [name for name in wanted if name not in ctx.enabled_plugins()])
        plugin.remove_from_config(ctx.config_path, [name for name in candidates(ctx) if name not in wanted])


def _fields(cls) -> List[Tuple[str, Any]]:
    """The settings of a plugin that setup asks about: fields marked with ``json_schema_extra={'setup': ...}``."""
    model = getattr(cls, 'settings', None)
    if model is None:
        return []
    return [(key, field) for key, field in model.model_fields.items()
            if isinstance(field.json_schema_extra, dict) and field.json_schema_extra.get('setup')]


def _choices(field) -> Optional[Tuple[Tuple[str, str], ...]]:
    if typing.get_origin(field.annotation) is not typing.Literal:
        return None
    labels = field.json_schema_extra.get('setup')
    labels = labels if isinstance(labels, dict) else {}
    return tuple((str(value), labels.get(value, str(value))) for value in typing.get_args(field.annotation))


def _validator(field):
    from pydantic import TypeAdapter, ValidationError
    adapter = TypeAdapter(field.annotation)

    def validate(text: str) -> Optional[str]:
        try:
            adapter.validate_python(text)
        except ValidationError as error:
            return error.errors()[0]['msg']
        return None

    return validate


class PeripheralOptionsStep(Step):
    name = 'peripheral_options'
    title = 'Options of the attached hardware'
    phase = 'peripherals'

    def _fields(self, ctx):
        found = candidates(ctx)
        return [(name, key, field) for name in chosen(ctx) for key, field in _fields(found[name])]

    def questions_for(self, ctx):
        enabled = ctx.enabled_plugins()
        questions = []
        for name, key, field in self._fields(ctx):
            current = enabled.get(name)
            current = current.get(key, field.default) if isinstance(current, dict) else field.default
            title = field.title or key
            choices = _choices(field)
            if choices:
                questions.append(Question(f'opt_{name}_{key}', f"{title} ({_label(name, candidates(ctx)[name])})",
                                          kind='choice', choices=choices, default=str(current)))
            elif field.annotation is bool:
                questions.append(Question(f'opt_{name}_{key}', f"{title} ({_label(name, candidates(ctx)[name])})",
                                          default=bool(current)))
            else:
                questions.append(Question(f'opt_{name}_{key}', f"{title} ({_label(name, candidates(ctx)[name])})",
                                          kind='text', default=str(current), validate=_validator(field),
                                          help=field.description or ''))
        return tuple(questions)

    def wanted(self, ctx):
        return bool(self._fields(ctx))

    def _answers(self, ctx):
        from pydantic import TypeAdapter
        for name, key, field in self._fields(ctx):
            answer = ctx.answers.get(f'opt_{name}_{key}')
            if answer is not None:
                yield name, key, TypeAdapter(field.annotation).validate_python(answer)

    def check(self, ctx):
        enabled = ctx.enabled_plugins()
        problems = []
        for name, key, value in self._answers(ctx):
            current = enabled.get(name)
            if isinstance(current, dict) and current.get(key) != value:
                problems.append(f"plugin '{name}': {key} is not {value}")
        return problems

    def apply(self, ctx):
        cfg = ctx.load_config()
        for name, key, value in self._answers(ctx):
            cfg.setndefault('plugins', name, value={})
            cfg.setn('plugins', name, key, value=value)
        lauschkiste.common.cfghandler.write_yaml(cfg, str(ctx.config_path))
