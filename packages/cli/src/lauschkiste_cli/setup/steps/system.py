"""Operating system: packages, Raspberry Pi settings, boot time, login message."""

from typing import List

import typer

import lauschkiste.common.paths
from lauschkiste_cli.setup.base import Context, Question, Step
from lauschkiste_cli.setup.steps.lauschkiste import public_port
from lauschkiste_cli.setup.system import SetupError

BUILD_PACKAGES = ['build-essential', 'python3-dev', 'libffi-dev']
RUNTIME_PACKAGES = ['alsa-utils', 'espeak', 'libportaudio2']
#: A desktop brings its own sound server; a Pi Lite image does not
AUDIO_PACKAGES = ['pipewire', 'pipewire-pulse', 'pipewire-audio', 'wireplumber', 'libspa-0.2-bluetooth']
#: piwheels' `av` (32-bit ARM) links against the system's ffmpeg libraries instead of bundling them
PIWHEELS_ARCHITECTURES = ('armv6', 'armv7')


class PackagesStep(Step):
    name = 'packages'
    title = 'System packages'
    questions = (
        Question('upgrade_os', 'Upgrade all operating system packages now (takes a while)?', default=False),
    )

    def relevant(self, ctx):
        return ctx.system.is_debian()

    def packages(self, ctx):
        pi = ctx.system.is_raspberry_pi()
        audio = AUDIO_PACKAGES if pi else []
        ffmpeg = ['ffmpeg'] if pi and ctx.system.architecture() in PIWHEELS_ARCHITECTURES else []
        return [*BUILD_PACKAGES, *RUNTIME_PACKAGES, *audio, *ffmpeg]

    def apply(self, ctx):
        pass


def _boot_wanted(ctx: Context):
    """What config.txt needs, by the rules of the board_raspberry_pi plugin; None without it."""
    try:
        from lauschkiste_plugin_board_raspberry_pi import bootconfig
    except ImportError:
        return None, None
    import lauschkiste.common.statefile
    cfg = ctx.load_config()
    rfid_path = lauschkiste.common.paths.resolve(cfg.getn('rfid', 'reader_config', default='settings/rfid.yaml'))
    want = bootconfig.wanted({'plugins': cfg.getn('plugins', default=None) or {}},
                             lauschkiste.common.statefile.read_yaml(rfid_path))
    return bootconfig, want


class RaspberryPiStep(Step):
    """Boot configuration (config.txt) for the hardware set up in Lauschkiste: sound card, I²C, SPI,
    power-off pin, on-chip audio. The settings come from the web app (board and device plugins)."""
    name = 'raspi'
    title = 'Raspberry Pi boot configuration'

    def relevant(self, ctx):
        return ctx.system.is_raspberry_pi()

    def packages(self, ctx):
        return ['liblgpio-dev', 'swig']

    def check(self, ctx):
        bootconfig, want = _boot_wanted(ctx)
        if bootconfig is None:
            return ['the board_raspberry_pi plugin package is not installed']
        config = ctx.system.read(ctx.system.boot_file('config.txt')) or ''
        return [f'config.txt: {problem}' for problem in bootconfig.pending(config, want)]

    def apply(self, ctx):
        system = ctx.system
        system.run('iwconfig', 'wlan0', 'power', 'off', root=True, check=False)
        bootconfig, want = _boot_wanted(ctx)
        if bootconfig is None:
            raise SetupError('the board_raspberry_pi plugin package is not installed')
        path = system.boot_file('config.txt')
        config = system.read(path) or ''
        wanted = bootconfig.render(config, want)
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

    def relevant(self, ctx):
        return ctx.system.is_raspberry_pi()

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


class WelcomeStep(Step):
    name = 'welcome'
    title = 'Login message'
    TARGET = '/etc/update-motd.d/99-lauschkiste-welcome'

    def relevant(self, ctx):
        return ctx.system.is_raspberry_pi()

    def _content(self, ctx) -> str:
        port = public_port(ctx)
        return lauschkiste.common.paths.resource('system', '99-lauschkiste-welcome').read_text().replace('@PORT@', str(port))

    def check(self, ctx) -> List[str]:
        return [] if ctx.system.read(self.TARGET) == self._content(ctx) else ['login message not installed or outdated']

    def apply(self, ctx):
        ctx.system.write(self.TARGET, self._content(ctx), root=True, mode=0o755)
