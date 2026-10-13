"""The sound card on the header of the device (the device's own hardware option)."""

from typing import Tuple

import lauschkiste.common.cfghandler
from lauschkiste_cli.setup.base import Context, Question, Step

NO_CARD = ('none', 'No sound card on the header (headphone jack, HDMI, USB or Bluetooth)')
DEVICE = 'device_raspberry_pi'


def _sound_cards(ctx: Context) -> Tuple[Tuple[str, str], ...]:
    try:
        from lauschkiste_plugin_device_raspberry_pi import bootconfig
    except ImportError:
        return (NO_CARD,)
    return (NO_CARD, *bootconfig.describe_cards().items())


def _detected_hat(ctx: Context):
    """The attached HAT that names itself (HAT EEPROM), None without one."""
    try:
        from lauschkiste_plugin_device_raspberry_pi import hat
    except ImportError:
        return None
    return hat.read_hat(ctx.system.read)


def _sound_card_default(ctx: Context) -> str:
    current = _current(ctx, DEVICE, 'sound_card', 'none')
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
    """The sound card on the header, an option of the Raspberry Pi device. What else is attached (pHAT BEAT, power
    button, battery monitor, ...) is chosen in the ``peripherals`` step. The boot configuration (``raspi``) follows
    from both."""
    name = 'hardware'
    title = 'Sound card on the header'
    needs = ('boot_config',)
    questions = (
        Question('hw_sound_card', "Which sound card sits on the header ('none' for a pHAT BEAT: it brings its own)?",
                 kind='choice', choices=_sound_cards, default=_sound_card_default, help=_sound_card_help),
    )

    def relevant(self, ctx):
        try:
            import lauschkiste_plugin_device_raspberry_pi  # noqa: F401
        except ImportError:
            return False
        return ctx.device_name() == DEVICE

    def check(self, ctx):
        current = ctx.enabled_plugins().get(DEVICE)
        wanted = ctx.answer('hw_sound_card', 'none')
        if isinstance(current, dict) and current.get('sound_card', 'none') != wanted:
            return [f"plugin '{DEVICE}': sound_card is not {wanted}"]
        return []

    def apply(self, ctx):
        cfg = ctx.load_config()
        cfg.setndefault('plugins', DEVICE, value={})
        cfg.setn('plugins', DEVICE, 'sound_card', value=ctx.answer('hw_sound_card', 'none'))
        lauschkiste.common.cfghandler.write_yaml(cfg, str(ctx.config_path))
