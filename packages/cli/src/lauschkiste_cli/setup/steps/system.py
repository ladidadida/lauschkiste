"""Operating system: packages, Raspberry Pi settings, boot time, login message."""

from typing import List

import typer

import lauschkiste.paths
from lauschkiste_cli.setup.base import Context, Question, Step
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
    import lauschkiste.statefile
    cfg = ctx.load_config()
    rfid_path = lauschkiste.paths.resolve(cfg.getn('rfid', 'reader_config', default='settings/rfid.yaml'))
    want = bootconfig.wanted({'plugins': cfg.getn('plugins', default=None) or {}},
                             lauschkiste.statefile.read_yaml(rfid_path))
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


class BootStep(Step):
    name = 'boot'
    title = 'Boot time optimisation'
    questions = (
        Question('optimize_boot', 'Optimise the boot time (quiet boot, unneeded services off)?', default=True),
        Question('disable_bluetooth', 'Disable Bluetooth (saves power and boot time)?', default=True,
                 when=lambda a: a.get('optimize_boot')),
        Question('disable_ipv6', 'Disable IPv6?', default=True, when=lambda a: a.get('optimize_boot')),
        Question('static_ip', 'Use the current IP address as static address (faster network start)?',
                 default=False, when=lambda a: a.get('optimize_boot') and not a.get('autohotspot')),
    )
    MARKER = '## Lauschkiste Boot Config'
    DHCP_MARKER = '## Lauschkiste DHCP Config'
    SERVICES = ['keyboard-setup.service', 'triggerhappy.service', 'triggerhappy.socket', 'raspi-config.service',
                'apt-daily.service', 'apt-daily-upgrade.service', 'apt-daily.timer', 'apt-daily-upgrade.timer']
    BLUETOOTH = ['hciuart.service', 'bluetooth.service']
    CMDLINE = ['consoleblank=1', 'logo.nologo', 'quiet', 'loglevel=0', 'plymouth.enable=0',
               'vt.global_cursor_default=0', 'plymouth.ignore-serial-consoles', 'splash', 'fastboot',
               'noatime', 'nodiratime', 'noram']
    IPV6 = 'ipv6.disable=1'

    def relevant(self, ctx):
        return ctx.system.is_raspberry_pi()

    def wanted(self, ctx):
        return bool(ctx.answer('optimize_boot'))

    def _services(self, ctx):
        return self.SERVICES + (self.BLUETOOTH if ctx.answer('disable_bluetooth') else [])

    def _cmdline_options(self, ctx):
        return self.CMDLINE + ([self.IPV6] if ctx.answer('disable_ipv6') else [])

    def check(self, ctx):
        system = ctx.system
        problems = [f'{unit} is enabled' for unit in self._services(ctx) if system.unit_enabled(unit)]
        if self.MARKER not in (system.read(system.boot_file('config.txt')) or ''):
            problems.append('boot splash screen is enabled')
        cmdline = (system.read(system.boot_file('cmdline.txt')) or '').split()
        missing = [option for option in self._cmdline_options(ctx) if option not in cmdline]
        if missing:
            problems.append(f"cmdline.txt lacks {' '.join(missing)}")
        if ctx.answer('static_ip') and not static_ip_configured(ctx):
            problems.append('no static IP address configured')
        return problems

    def apply(self, ctx):
        system = ctx.system
        for unit in self._services(ctx):
            if system.unit_enabled(unit):
                system.run('systemctl', 'disable', unit, root=True, check=False)
        system.append_block(system.boot_file('config.txt'), self.MARKER, 'disable_splash=1', root=True)
        path = system.boot_file('cmdline.txt')
        cmdline = (system.read(path) or '').split()
        missing = [option for option in self._cmdline_options(ctx) if option not in cmdline]
        if missing:
            system.write(path, ' '.join(cmdline + missing) + '\n', root=True)
        if ctx.answer('static_ip') and not static_ip_configured(ctx):
            configure_static_ip(ctx)


def current_route(ctx: Context) -> dict:
    """Interface, address and gateway of the default route."""
    words = ctx.system.output('ip', 'route', 'get', '8.8.8.8').split()
    keys = {'dev': 'interface', 'src': 'address', 'via': 'gateway'}
    return {keys[word]: words[i + 1] for i, word in enumerate(words[:-1]) if word in keys}


def _nm_profile(ctx: Context, interface: str) -> str:
    for line in ctx.system.output('nmcli', '-g', 'DEVICE,CONNECTION', 'device', 'status').splitlines():
        device, _, connection = line.partition(':')
        if device == interface:
            return connection
    return ''


def static_ip_configured(ctx: Context) -> bool:
    system = ctx.system
    if system.unit_enabled('NetworkManager.service'):
        profile = _nm_profile(ctx, current_route(ctx).get('interface', ''))
        return bool(profile) and system.output('nmcli', '-g', 'ipv4.method', 'connection', 'show', profile) == 'manual'
    return BootStep.DHCP_MARKER in (system.read('/etc/dhcpcd.conf') or '')


def configure_static_ip(ctx: Context) -> None:
    system = ctx.system
    route = current_route(ctx)
    if not {'interface', 'address', 'gateway'} <= set(route):
        raise SetupError(f'Could not determine the current network route: {route}')
    address, gateway = f"{route['address']}/24", route['gateway']
    if system.unit_enabled('NetworkManager.service'):
        profile = _nm_profile(ctx, route['interface'])
        system.run('nmcli', 'connection', 'modify', profile, 'ipv4.method', 'manual', 'ipv4.address', address,
                   'ipv4.gateway', gateway, 'ipv4.dns', gateway, root=True)
    else:
        system.append_block('/etc/dhcpcd.conf', BootStep.DHCP_MARKER,
                            f"interface {route['interface']}\nstatic ip_address={address}\n"
                            f"static routers={gateway}\nstatic domain_name_servers={gateway}\nnoarp", root=True)


class WelcomeStep(Step):
    name = 'welcome'
    title = 'Login message'
    TARGET = '/etc/update-motd.d/99-lauschkiste-welcome'

    def relevant(self, ctx):
        return ctx.system.is_raspberry_pi()

    def _content(self) -> str:
        return lauschkiste.paths.resource('system', '99-lauschkiste-welcome').read_text()

    def check(self, ctx) -> List[str]:
        return [] if ctx.system.read(self.TARGET) == self._content() else ['login message not installed']

    def apply(self, ctx):
        ctx.system.write(self.TARGET, self._content(), root=True, mode=0o755)
