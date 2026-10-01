"""Operating system: packages, Raspberry Pi settings, boot time, login message."""

import re
from typing import List

import typer

import jukebox.paths
from jukebox_cli.setup.base import Context, Question, Step
from jukebox_cli.setup.system import SetupError

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


HIFIBERRY_BOARDS = {
    'hifiberry-dac': 'DAC (HiFiBerry MiniAmp, I2S PCM5102A DAC)',
    'hifiberry-dacplus': 'HiFiBerry DAC+ Standard/Pro/Amp2',
    'hifiberry-dacplushd': 'HiFiBerry DAC2 HD',
    'hifiberry-dacplusadc': 'HiFiBerry DAC+ ADC',
    'hifiberry-dacplusadcpro': 'HiFiBerry DAC+ ADC Pro',
    'hifiberry-digi': 'HiFiBerry Digi+',
    'hifiberry-digi-pro': 'HiFiBerry Digi+ Pro',
    'hifiberry-amp': 'HiFiBerry Amp+ (not Amp2)',
    'hifiberry-amp3': 'HiFiBerry Amp3',
}
HIFIBERRY_OVERLAY = re.compile(r'^dtoverlay=(hifiberry-[\w-]+)\s*$', re.MULTILINE)


def _configured_sound_card(ctx: Context) -> str:
    match = HIFIBERRY_OVERLAY.search(ctx.system.read(ctx.system.boot_file('config.txt')) or '')
    return match.group(1) if match else 'none'


def _validate_sound_card(value: str):
    if value == 'none' or value in HIFIBERRY_BOARDS:
        return None
    return f"Choose one of: none, {', '.join(HIFIBERRY_BOARDS)}"


class RaspberryPiStep(Step):
    name = 'raspi'
    title = 'Raspberry Pi settings'
    questions = (
        Question('sound_card', 'HifiBerry (or compatible I2S DAC) sound card', kind='text',
                 default=_configured_sound_card, validate=_validate_sound_card,
                 help='none, or one of: ' + ', '.join(f'{key} ({name})' for key, name in HIFIBERRY_BOARDS.items())),
        Question('disable_onboard_audio', "Disable the Pi's on-chip audio (headphone jack)?", default=False,
                 when=lambda a: a.get('sound_card', 'none') == 'none',
                 help='Recommended with an external sound card (USB, ...); '
                      'keep it for Bluetooth-only speakers. config.txt is backed up first.'),
    )
    AUDIO_ON = re.compile(r'^(dtparam=([^,\n]*,)*)audio=(on|true|yes|1)(.*)$', re.MULTILINE)

    def relevant(self, ctx):
        return ctx.system.is_raspberry_pi()

    def packages(self, ctx):
        return ['liblgpio-dev', 'swig']

    def _card(self, ctx) -> str:
        return ctx.answer('sound_card') or 'none'

    def _onboard_off(self, ctx) -> bool:
        return self._card(ctx) != 'none' or bool(ctx.answer('disable_onboard_audio'))

    def _config(self, ctx, config: str) -> str:
        """config.txt as this step wants it."""
        if self._onboard_off(ctx):
            config = self.AUDIO_ON.sub(r'\1audio=off\4', config)
        card = self._card(ctx)
        if card != 'none' and HIFIBERRY_OVERLAY.findall(config) != [card]:
            config = HIFIBERRY_OVERLAY.sub('', config).rstrip('\n') + f'\ndtoverlay={card}\n'
            config = re.sub(r'\n{3,}', '\n\n', config)
        return config

    def check(self, ctx):
        config = ctx.system.read(ctx.system.boot_file('config.txt')) or ''
        problems = []
        if self._onboard_off(ctx) and self.AUDIO_ON.search(config):
            problems.append('on-chip audio is enabled in config.txt')
        if self._card(ctx) != 'none' and HIFIBERRY_OVERLAY.findall(config) != [self._card(ctx)]:
            problems.append(f'config.txt does not load (only) the {self._card(ctx)} overlay')
        return problems

    def apply(self, ctx):
        system = ctx.system
        system.run('iwconfig', 'wlan0', 'power', 'off', root=True, check=False)
        path = system.boot_file('config.txt')
        config = system.read(path) or ''
        wanted = self._config(ctx, config)
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
                 default=True, when=lambda a: a.get('optimize_boot') and not a.get('autohotspot')),
    )
    MARKER = '## Jukebox Boot Config'
    DHCP_MARKER = '## Jukebox DHCP Config'
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
    TARGET = '/etc/update-motd.d/99-rpi-jukebox-rfid-welcome'

    def relevant(self, ctx):
        return ctx.system.is_raspberry_pi()

    def _content(self) -> str:
        return jukebox.paths.resource('system', '99-rpi-jukebox-rfid-welcome').read_text()

    def check(self, ctx) -> List[str]:
        return [] if ctx.system.read(self.TARGET) == self._content() else ['login message not installed']

    def apply(self, ctx):
        ctx.system.write(self.TARGET, self._content(), root=True, mode=0o755)
