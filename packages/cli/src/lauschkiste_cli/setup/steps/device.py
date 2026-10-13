"""The device: which kind of machine this is, chosen first; what the other steps offer depends on it."""

from typing import List, Optional, Set

import lauschkiste.contract.plugins as plugins
from lauschkiste_cli import plugin
from lauschkiste_cli.setup.base import Context, Question, Step
from lauschkiste_cli.setup.steps import extra_plugins
from lauschkiste_cli.setup.system import SetupError

NONE = 'none'
OWN = 'own'


def _device_classes() -> dict:
    classes = {}
    for name, entry_point in plugins.installed().items():
        cls, _ = plugins.load(entry_point)
        if cls is not None and 'device' in getattr(cls, 'provides', ()):
            classes[name] = cls
    return classes


def _own_spec(ctx: Context) -> Optional[str]:
    specs = extra_plugins.parse_specs(str(ctx.answer('device_plugin', '') or ''))
    return specs[0] if specs else None


def resolve(ctx: Context) -> Optional[str]:
    """The name of the device plugin: the answer, else the enabled one, else the one that recognises this machine."""
    classes = _device_classes()
    chosen = ctx.answer('device')
    if chosen == NONE:
        return None
    if chosen == OWN:
        spec = _own_spec(ctx)
        return next((name for name in extra_plugins.installed_by(spec) if name in classes), None) if spec else None
    if chosen:
        return chosen
    for name in ctx.enabled_plugins():
        if name in classes:
            return name
    detected = plugins.detected_devices(ctx.system.read)
    return detected[0]['name'] if detected else None


def capabilities(ctx: Context) -> Set[str]:
    cls = _device_classes().get(resolve(ctx) or '')
    return set(getattr(cls, 'provides', ())) if cls is not None else set()


def _choices(ctx: Context):
    detected = {entry['name']: entry['model'] for entry in plugins.detected_devices(ctx.system.read)}
    choices = []
    for name, cls in sorted(_device_classes().items()):
        label = getattr(cls, 'title', '') or plugins.readable(name)
        choices.append((name, f"{label} (this machine: {detected[name]})" if name in detected else label))
    return [*choices, (OWN, 'A device plugin of my own (a package, github:owner/repo or a URL)'),
            (NONE, 'None of these: change nothing on this system')]


def _default(ctx: Context) -> str:
    return resolve(ctx) or NONE


def _validate_own(text: str) -> Optional[str]:
    specs = extra_plugins.parse_specs(text) if text.strip() else []
    return None if len(specs) == 1 else 'Enter exactly one package name, github:owner/repo link or URL.'


class DeviceStep(Step):
    name = 'device'
    title = 'Device'
    questions = (
        Question('device', 'What kind of machine is this?', kind='choice', choices=_choices, default=_default,
                 help='The device decides which of the following questions are asked: a Raspberry Pi can be set up '
                      'for the box, a computer that is used for other things is left as it is.'),
        Question('device_plugin', 'The device plugin to install (package name, github:owner/repo[@tag] or URL)',
                 kind='text', default='', validate=_validate_own, when=lambda answers: answers.get('device') == OWN,
                 help='A plugin runs with the rights of your user: install only what you trust.'),
    )

    def _others(self, ctx: Context, keep: Optional[str]) -> List[str]:
        return [name for name in ctx.enabled_plugins() if name in _device_classes() and name != keep]

    def check(self, ctx):
        wanted = resolve(ctx)
        enabled = ctx.enabled_plugins()
        problems = [f"device plugin '{name}' is enabled but another device was chosen" for name in
                    self._others(ctx, wanted)]
        if wanted is not None and wanted not in enabled:
            problems.append(f"device plugin '{wanted}' is not enabled")
        if ctx.answer('device') == OWN and wanted is None:
            problems.append('the device plugin of your own is not installed yet')
        return problems

    def apply(self, ctx):
        if ctx.answer('device') == OWN and resolve(ctx) is None:
            spec = _own_spec(ctx)
            extra_plugins.install_spec(ctx, spec)
            if resolve(ctx) is None:
                raise SetupError(f"'{spec}' provides no device plugin")
        wanted = resolve(ctx)
        for name in self._others(ctx, wanted):
            plugin.remove_from_config(ctx.config_path, [name])
        if wanted is not None:
            extras = plugin.plugin_extras(wanted)
            if extras:
                plugin.install_requirements(extras)
            plugin.add_to_config(ctx.config_path, [wanted])
