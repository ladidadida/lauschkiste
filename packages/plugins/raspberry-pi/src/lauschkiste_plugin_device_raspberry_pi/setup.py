"""The setup steps of the Raspberry Pi device: sound card, quiet boot and the boot configuration."""

from typing import Tuple

import typer

import lauschkiste.common.cfghandler
import lauschkiste.common.paths
import lauschkiste.common.statefile
from lauschkiste_cli.setup.base import Context, Question, Step

from lauschkiste_plugin_device_raspberry_pi import bootconfig, hat

NO_CARD = ('none', 'No sound card on the header (headphone jack, HDMI, USB or Bluetooth)')
DEVICE = 'device_raspberry_pi'


def _sound_cards(ctx: Context) -> Tuple[Tuple[str, str], ...]:
    return (NO_CARD, *bootconfig.describe_cards().items())


def _detected_hat(ctx: Context):
    """The attached HAT that names itself (HAT EEPROM), None without one."""
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
    position = 'early'
    questions = (
        Question('hw_sound_card', "Which sound card sits on the header ('none' for a pHAT BEAT: it brings its own)?",
                 kind='choice', choices=_sound_cards, default=_sound_card_default, help=_sound_card_help),
    )

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


def _boot_wanted(ctx: Context):
    """What config.txt needs, by the rules of this plugin."""
    cfg = ctx.load_config()
    rfid_path = lauschkiste.common.paths.resolve(cfg.getn('rfid', 'reader_config', default='settings/rfid.yaml'))
    return bootconfig.wanted({'plugins': cfg.getn('plugins', default=None) or {}},
                             lauschkiste.common.statefile.read_yaml(rfid_path))


class RaspberryPiStep(Step):
    """Boot configuration (config.txt) for the hardware set up in Lauschkiste: sound card, I²C, SPI,
    power-off pin, on-chip audio. The settings come from the web app (device and peripheral plugins)."""
    name = 'raspi'
    title = 'Raspberry Pi boot configuration'
    needs = ('boot_config',)
    position = 'late'

    def packages(self, ctx):
        return ['liblgpio-dev', 'swig']

    def check(self, ctx):
        config = ctx.system.read(ctx.system.boot_file('config.txt')) or ''
        return [f'config.txt: {problem}' for problem in bootconfig.pending(config, _boot_wanted(ctx))]

    def apply(self, ctx):
        system = ctx.system
        system.run('iwconfig', 'wlan0', 'power', 'off', root=True, check=False)
        path = system.boot_file('config.txt')
        config = system.read(path) or ''
        wanted = bootconfig.render(config, _boot_wanted(ctx))
        if wanted != config:
            system.write(f'{path}.backup', config, root=True)
            system.write(path, wanted, root=True)
            typer.echo('    config.txt changed: reboot for it to take effect.')
            ctx.notes.append('Reboot the box (sudo reboot) so that the changed boot configuration takes effect.')


class BootStep(Step):
    """A quieter boot for a box with a screen: no boot messages or logo, a few first-boot services off.
    Nothing here touches the network."""
    name = 'boot'
    title = 'Quiet boot'
    needs = ('boot_config',)
    position = 'early'
    questions = (
        Question('optimize_boot', 'Make the boot quiet (no boot messages or logo, a few first-boot services off)?',
                 default=False,
                 help='Only cosmetic and a little faster; it changes the kernel command line. A box without a screen '
                      'does not need it.'),
        Question('disable_bluetooth', 'Also switch Bluetooth off (saves a little power)?', default=False,
                 when=lambda a: a.get('optimize_boot'),
                 help='Leave it on if you want to use Bluetooth speakers or headphones.'),
    )
    MARKER = '## Lauschkiste Boot Config'
    SERVICES = ['keyboard-setup.service', 'triggerhappy.service', 'triggerhappy.socket', 'raspi-config.service']
    BLUETOOTH = ['hciuart.service', 'bluetooth.service']
    CMDLINE = ['consoleblank=1', 'logo.nologo', 'quiet', 'loglevel=0', 'plymouth.enable=0',
               'vt.global_cursor_default=0', 'plymouth.ignore-serial-consoles', 'splash']

    def wanted(self, ctx):
        return bool(ctx.answer('optimize_boot'))

    def _services(self, ctx):
        return self.SERVICES + (self.BLUETOOTH if ctx.answer('disable_bluetooth') else [])

    def check(self, ctx):
        system = ctx.system
        problems = [f'{unit} is enabled' for unit in self._services(ctx) if system.unit_enabled(unit)]
        if self.MARKER not in (system.read(system.boot_file('config.txt')) or ''):
            problems.append('boot splash screen is enabled')
        cmdline = (system.read(system.boot_file('cmdline.txt')) or '').split()
        missing = [option for option in self.CMDLINE if option not in cmdline]
        if missing:
            problems.append(f"cmdline.txt lacks {' '.join(missing)}")
        return problems

    def apply(self, ctx):
        system = ctx.system
        for unit in self._services(ctx):
            if system.unit_enabled(unit):
                system.run('systemctl', 'disable', unit, root=True, check=False)
        system.append_block(system.boot_file('config.txt'), self.MARKER, 'disable_splash=1', root=True)
        path = system.boot_file('cmdline.txt')
        cmdline = (system.read(path) or '').split()
        missing = [option for option in self.CMDLINE if option not in cmdline]
        if missing:
            system.write(path, ' '.join(cmdline + missing) + '\n', root=True)
            ctx.notes.append('The kernel command line changed: if the box does not come back after the reboot, '
                             'remove the options from cmdline.txt on the boot partition of the SD card.')


def steps():
    return [HardwareStep(), BootStep(), RaspberryPiStep()]
