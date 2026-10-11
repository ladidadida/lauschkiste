"""The hardware that is connected to the box: sound card, pHAT BEAT, power button, battery monitor."""

from typing import Dict, List, Tuple

import lauschkiste.cfghandler
from lauschkiste_cli.setup.base import Context, Question, Step

NO_CARD = ('none', 'No sound card on the header (headphone jack, HDMI, USB or Bluetooth)')
BATTERY_DRIVERS: Tuple[Tuple[str, str], ...] = (
    ('none', 'No battery monitor'),
    ('max17048', 'MAX17048 fuel gauge (Adafruit, SparkFun LiPo boards)'),
    ('ina219', 'INA219 current/voltage sensor'),
)
BOARD = 'board_raspberry_pi'


def _sound_cards(ctx: Context) -> Tuple[Tuple[str, str], ...]:
    try:
        from lauschkiste_plugin_board_raspberry_pi import bootconfig
    except ImportError:
        return (NO_CARD,)
    return (NO_CARD, *bootconfig.describe_cards().items())


def _detected_hat(ctx: Context):
    """The attached HAT that names itself (HAT EEPROM), None without one."""
    try:
        from lauschkiste_plugin_board_raspberry_pi import hat
    except ImportError:
        return None
    return hat.read_hat(ctx.system.read)


def _sound_card_default(ctx: Context) -> str:
    current = _current(ctx, BOARD, 'sound_card', 'none')
    detected = _detected_hat(ctx)
    return current if current != 'none' or detected is None or detected.sound_card is None else detected.sound_card


def _sound_card_help(ctx: Context) -> str:
    detected = _detected_hat(ctx)
    if detected is None:
        return ''
    if detected.sound_card is None:
        return f'A board on the header reports itself as {detected.label}; it is not a sound card Lauschkiste knows.'
    return f'Detected: {detected.label}.'


def _current(ctx: Context, plugin: str, key: str, default: str) -> str:
    settings = ctx.enabled_plugins().get(plugin)
    return str(settings.get(key, default)) if isinstance(settings, dict) else default


class HardwareStep(Step):
    """Which hardware sits on the board; the answers decide which plugins are enabled. The boot configuration
    (``raspi``) and the extras of the plugins (``plugins``) follow from that."""
    name = 'hardware'
    title = 'Connected hardware'
    questions = (
        Question('hw_phat_beat', 'Is a Pimoroni pHAT BEAT (Pirate Radio) attached?',
                 default=lambda ctx: 'phat_beat' in ctx.enabled_plugins(),
                 help='Its sound card, buttons and LEDs are set up with it.'),
        Question('hw_sound_card', 'Which sound card sits on the header?', kind='choice', choices=_sound_cards,
                 default=_sound_card_default, help=_sound_card_help,
                 when=lambda answers: not answers.get('hw_phat_beat')),
        Question('hw_power_button', 'Is a power button attached (Pimoroni OnOff SHIM)?',
                 default=lambda ctx: 'power_button' in ctx.enabled_plugins()),
        Question('hw_battery', 'Is a battery monitor attached?', kind='choice', choices=BATTERY_DRIVERS,
                 default=lambda ctx: _current(ctx, 'battery', 'driver', 'max17048') if 'battery' in ctx.enabled_plugins()
                 else 'none'),
    )

    def relevant(self, ctx):
        if not ctx.system.is_raspberry_pi():
            return False
        try:
            import lauschkiste_plugin_board_raspberry_pi  # noqa: F401
        except ImportError:
            return False
        return True

    def _wanted(self, ctx: Context) -> Tuple[Dict[str, Dict], List[str]]:
        """(plugins to enable with the settings this step owns, plugins to disable)."""
        enable: Dict[str, Dict] = {BOARD: {}}
        phat = bool(ctx.answer('hw_phat_beat'))
        if phat:
            enable['phat_beat'] = {}
        else:
            enable[BOARD] = {'sound_card': ctx.answer('hw_sound_card', 'none')}
        if ctx.answer('hw_power_button'):
            enable['power_button'] = {}
        battery = ctx.answer('hw_battery', 'none')
        if battery != 'none':
            enable['battery'] = {'driver': battery}
        disable = [name for name in ('phat_beat', 'power_button', 'battery') if name not in enable]
        return enable, disable

    def check(self, ctx):
        enable, disable = self._wanted(ctx)
        enabled = ctx.enabled_plugins()
        problems = [f"plugin '{name}' is not enabled" for name in enable if name not in enabled]
        problems += [f"plugin '{name}' is enabled but no such hardware was chosen" for name in disable
                     if name in enabled]
        for name, settings in enable.items():
            current = enabled.get(name)
            for key, value in settings.items():
                if isinstance(current, dict) and current.get(key, 'none' if key == 'sound_card' else None) != value:
                    problems.append(f"plugin '{name}': {key} is not {value}")
        return problems

    def apply(self, ctx):
        enable, disable = self._wanted(ctx)
        cfg = ctx.load_config()
        for name, settings in enable.items():
            cfg.setndefault('plugins', name, value={})
            for key, value in settings.items():
                cfg.setn('plugins', name, key, value=value)
        plugins = cfg.getn('plugins', default=None)
        for name in disable:
            if isinstance(plugins, dict) and name in plugins:
                del plugins[name]
        lauschkiste.cfghandler.write_yaml(cfg, str(ctx.config_path))
