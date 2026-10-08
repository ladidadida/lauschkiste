"""Optional features: MPD, Samba, kiosk mode, WiFi hotspot, audio outputs."""

import re

import click
import typer

import lauschkiste.cfghandler
import lauschkiste.paths
from lauschkiste_cli import plugin
from lauschkiste_cli.setup import samba
from lauschkiste_cli.setup.base import Question, Step
from lauschkiste_cli.setup.system import SetupError, StepSkipped


class MpdStep(Step):
    name = 'mpd'
    title = 'MPD (Music Player Daemon) as user service'
    questions = (
        Question('mpd', 'Use MPD as player backend instead of the built-in player?', default=False,
                 help='Only needed to keep an existing MPD setup; the built-in player needs no extra service.'),
    )
    CONF = '~/.config/mpd/mpd.conf'

    def wanted(self, ctx):
        return bool(ctx.answer('mpd'))

    def packages(self, ctx):
        return ['mpd', 'mpc']

    @staticmethod
    def library(ctx):
        return lauschkiste.paths.library_dir(ctx.load_config().getn('library', 'path', default=None))

    def conf(self, ctx) -> str:
        template = lauschkiste.paths.resource('default-settings', 'mpd.default.conf').read_text()
        return (template.replace('%%LAUSCHKISTE_LIBRARY_PATH%%', str(self.library(ctx)))
                .replace('%%LAUSCHKISTE_PLAYLISTS_PATH%%', str(lauschkiste.paths.resolve('playlists'))))

    def check(self, ctx):
        system = ctx.system
        problems = []
        if system.read(self.CONF) != self.conf(ctx):
            problems.append(f'{self.CONF} is missing or differs from the Lauschkiste template')
        problems += [f'system-wide {unit} is enabled' for unit in ('mpd.socket', 'mpd.service')
                     if system.unit_enabled(unit)]
        problems += [f'user {unit} is not enabled' for unit in ('mpd.socket', 'mpd.service')
                     if not system.unit_enabled(unit, user=True)]
        return problems

    def apply(self, ctx):
        system = ctx.system
        for unit in ('mpd.socket', 'mpd.service'):
            system.run('systemctl', 'disable', '--now', unit, root=True, check=False)
        current = system.read(self.CONF)
        if current is not None and current != self.conf(ctx):
            system.write(self.CONF + '.backup', current)
        for folder in (self.library(ctx), lauschkiste.paths.resolve('playlists')):
            folder.mkdir(parents=True, exist_ok=True)
        system.write(self.CONF, self.conf(ctx))
        system.run('systemctl', '--user', 'daemon-reload')
        system.run('systemctl', '--user', 'enable', 'mpd.socket', 'mpd.service')


class SambaStep(Step):
    name = 'samba'
    title = 'Samba share of the library'
    questions = (
        Question('samba', 'Share the library (music and audiobooks) on the network via Samba (Windows/macOS file sharing)?',
                 default=False,
                 help='Not needed for uploading music: the web app can do that too.'),
    )

    def wanted(self, ctx):
        return bool(ctx.answer('samba'))

    def packages(self, ctx):
        return ['samba', 'samba-common-bin']

    def prepare(self, ctx):
        ctx.system.run('debconf-set-selections', root=True, input='samba-common samba-common/dhcp boolean false\n',
                       quiet=True, check=False)

    def _library_folder(self, ctx) -> str:
        return str(lauschkiste.paths.library_dir(ctx.load_config().getn('library', 'path', default=None)))

    def check(self, ctx):
        problems = []
        if samba.current_block(ctx.system) is None:
            problems.append('no Lauschkiste share in smb.conf')
        elif not samba.is_current(ctx.system, self._library_folder(ctx)):
            problems.append('the Lauschkiste share in smb.conf is outdated')
        if not samba.has_user(ctx.system):
            problems.append(f'no Samba user {ctx.system.user}')
        return problems

    def _ask_password(self, ctx) -> str:
        while True:
            password = typer.prompt(f'Samba password for {ctx.system.user} (at least {samba.MIN_PASSWORD} characters)',
                                    hide_input=True, confirmation_prompt=True)
            if len(password) >= samba.MIN_PASSWORD:
                return password
            typer.echo(f'The password needs at least {samba.MIN_PASSWORD} characters.')

    def apply(self, ctx):
        if not samba.has_user(ctx.system):
            if ctx.assume_yes:
                raise StepSkipped("choosing the Samba password is interactive; run 'lauschctl setup samba' later "
                                  "or set it in the web app")
            samba.set_password(ctx.system, self._ask_password(ctx))
        samba.share(ctx.system, self._library_folder(ctx))
        plugin.add_to_config(ctx.config_path, ['samba'])


class KioskStep(Step):
    name = 'kiosk'
    title = 'Kiosk mode (web app on an attached screen)'
    questions = (
        Question('kiosk', 'Show the web app full-screen on an attached display after boot?', default=False,
                 help='Installs a minimal X server, openbox and Chromium, not a full desktop.'),
    )
    MARKER = '## Lauschkiste Kiosk Mode'
    BASHRC = '~/.bashrc'
    AUTOSTART = '/etc/xdg/openbox/autostart'
    AUTOLOGIN = '/etc/systemd/system/getty@tty1.service.d/autologin.conf'

    def relevant(self, ctx):
        return ctx.system.architecture() != 'armv6' and ctx.system.is_debian()

    def wanted(self, ctx):
        return bool(ctx.answer('kiosk'))

    def _chromium(self, ctx):
        return 'chromium' if ctx.system.architecture() == 'x86_64' else 'chromium-browser'

    def _update_check_file(self, ctx):
        if self._chromium(ctx) == 'chromium':
            return '/etc/chromium.d/01-disable-update-check'
        return '/etc/chromium-browser/customizations/01-disable-update-check'

    def packages(self, ctx):
        return ['xserver-xorg', 'x11-xserver-utils', 'xinit', 'openbox', self._chromium(ctx)]

    def check(self, ctx):
        system = ctx.system
        problems = [f'{path} is not set up' for path in (self.BASHRC, self.AUTOSTART, self._update_check_file(ctx))
                    if self.MARKER not in (system.read(path) or '')]
        if system.is_raspberry_pi() and not system.exists(self.AUTOLOGIN):
            problems.append('console autologin is not enabled')
        return problems

    def apply(self, ctx):
        system = ctx.system
        port = ctx.load_config().getn('api', 'port', default=5556)
        system.append_block(self.BASHRC, self.MARKER,
                            '[[ -z $DISPLAY && $XDG_VTNR -eq 1 ]] && startx -- -nocursor')
        system.append_block(self.AUTOSTART, self.MARKER, (
            'xset s off\n'
            'xset s noblank\n'
            'xset -dpms\n'
            "sed -i 's/\"exited_cleanly\":false/\"exited_cleanly\":true/' ~/.config/chromium/'Local State'\n"
            "sed -i 's/\"exited_cleanly\":false/\"exited_cleanly\":true/; "
            "s/\"exit_type\":\"[^\"]\\+\"/\"exit_type\":\"Normal\"/' ~/.config/chromium/Default/Preferences\n"
            f'{self._chromium(ctx)} http://localhost:{port} --disable-infobars --disable-pinch --disable-translate '
            '--kiosk --noerrdialogs --no-first-run'), root=True)
        system.write(self._update_check_file(ctx),
                     f'{self.MARKER}\nCHROMIUM_FLAGS="${{CHROMIUM_FLAGS}} --check-for-update-interval=31536000"\n',
                     root=True)
        if system.is_raspberry_pi() and not system.exists(self.AUTOLOGIN):
            system.run('raspi-config', 'nonint', 'do_boot_behaviour', 'B2', root=True)


def _validate_ssid(value):
    return None if 1 <= len(value) <= 32 else 'The SSID must have 1 to 32 characters.'


def _validate_password(value):
    return None if 8 <= len(value) <= 63 else 'The password must have 8 to 63 characters.'


def _validate_ip(value):
    return None if re.fullmatch(r'(\d{1,3}\.){3}\d{1,3}', value) else 'Please enter an IPv4 address like 10.0.0.1.'


class AutohotspotStep(Step):
    name = 'autohotspot'
    title = 'WiFi hotspot when no known WiFi is in range'
    questions = (
        Question('autohotspot', 'Open a WiFi hotspot when no known WiFi is in range?', default=False,
                 help='Lets you reach Lauschkiste without a network. Replaces the static IP option.'),
        Question('autohotspot_ssid', 'Hotspot name (SSID)', kind='text', validate=_validate_ssid,
                 default=lambda ctx: f"Lauschkiste_{ctx.system.output('hostname')}"[:32],
                 when=lambda a: a.get('autohotspot')),
        Question('autohotspot_password', 'Hotspot password', kind='text', default='PlayItLoud!',
                 validate=_validate_password, when=lambda a: a.get('autohotspot')),
        Question('autohotspot_ip', 'Hotspot IP address', kind='text', default='10.0.0.1',
                 validate=_validate_ip, when=lambda a: a.get('autohotspot')),
    )
    PROFILE = 'Lauschkiste_Hotspot'
    SCRIPT = '/usr/bin/autohotspot'
    SERVICE = 'autohotspot.service'
    TIMER = 'autohotspot.timer'
    INTERFACES = '/etc/network/interfaces'

    def relevant(self, ctx):
        return ctx.system.unit_enabled('NetworkManager.service') and ctx.system.is_raspberry_pi()

    def wanted(self, ctx):
        return bool(ctx.answer('autohotspot'))

    def packages(self, ctx):
        return ['iw']

    def _interface(self, ctx) -> str:
        match = re.search(r'Interface\s+(\S+)', ctx.system.output('iw', 'dev'))
        return match.group(1) if match else 'wlan0'

    def _files(self, ctx) -> dict:
        def template(name):
            return lauschkiste.paths.resource('autohotspot', 'NetworkManager', name).read_text()

        ip = ctx.answer('autohotspot_ip')
        values = {
            'WIFI_INTERFACE': self._interface(ctx),
            'AUTOHOTSPOT_PROFILE': self.PROFILE,
            'AUTOHOTSPOT_SSID': ctx.answer('autohotspot_ssid'),
            'AUTOHOTSPOT_PASSWORD': ctx.answer('autohotspot_password'),
            'AUTOHOTSPOT_IP': ip,
            'IP_WITHOUT_LAST_SEGMENT': ip.rsplit('.', 1)[0],
            'AUTOHOTSPOT_TIMER_NAME': self.TIMER,
            'AUTOHOTSPOT_SCRIPT': self.SCRIPT,
            'AUTOHOTSPOT_SERVICE': self.SERVICE,
        }

        def fill(text):
            return re.sub(r'%%(\w+)%%', lambda m: str(values[m.group(1)]), text)

        return {
            self.SCRIPT: fill(template('autohotspot')),
            f'/etc/systemd/system/{self.SERVICE}': fill(template('autohotspot.service')),
            f'/etc/systemd/system/{self.TIMER}': fill(template('autohotspot.timer')),
        }

    def check(self, ctx):
        problems = [f'{path} is missing or outdated' for path, content in self._files(ctx).items()
                    if ctx.system.read(path) != content]
        if not ctx.system.unit_enabled(self.TIMER):
            problems.append(f'{self.TIMER} is not enabled')
        return problems

    def apply(self, ctx):
        system = ctx.system
        if system.read(self.INTERFACES) and not system.exists(self.INTERFACES + '.orig'):
            system.write(self.INTERFACES + '.orig', system.read(self.INTERFACES) or '', root=True)
        system.write(self.INTERFACES, '', root=True)
        for path, content in self._files(ctx).items():
            system.write(path, content, root=True, mode=0o755 if path == self.SCRIPT else 0o644)
        system.run('systemctl', 'daemon-reload', root=True)
        system.run('systemctl', 'unmask', self.SERVICE, self.TIMER, root=True)
        system.run('systemctl', 'disable', self.SERVICE, root=True, check=False)
        system.run('systemctl', 'enable', self.TIMER, root=True)
        if not system.unit_enabled(self.TIMER):
            raise SetupError(f'{self.TIMER} could not be enabled')


class AudioStep(Step):
    name = 'audio'
    title = 'Audio outputs'
    questions = (
        Question('audio', 'Choose the audio outputs now (otherwise the system default output is used)?',
                 default=False, help='A second output (e.g. Bluetooth headphones) can be switched to in the web app.'),
    )

    def wanted(self, ctx):
        return bool(ctx.answer('audio'))

    def check(self, ctx):
        cfg = ctx.load_config()
        if not cfg.getn('volume', 'outputs', 'primary', 'pulse_sink_name', default=None):
            return ['no primary audio output chosen']
        return []

    def _sinks(self):
        import pulsectl
        try:
            with pulsectl.Pulse('lauschkiste-setup') as pulse:
                return [(sink.name, sink.description) for sink in pulse.sink_list()]
        except pulsectl.PulseError as error:
            raise SetupError(f'no PulseAudio/PipeWire server reachable: {error}') from None

    def apply(self, ctx):
        if ctx.assume_yes:
            raise StepSkipped("choosing the outputs is interactive; run 'lauschctl setup audio' later")
        sinks = self._sinks()
        if not sinks:
            raise SetupError('the sound server reports no audio outputs')
        for index, (name, description) in enumerate(sinks):
            typer.echo(f"{index:2d}: {description}  ({name})")
        primary = typer.prompt('Primary output', default=0, type=click.IntRange(0, len(sinks) - 1))
        secondary = -1
        if len(sinks) > 1:
            secondary = typer.prompt('Secondary output (-1: none)', default=-1,
                                     type=click.IntRange(-1, len(sinks) - 1))
        outputs = {'primary': {'alias': sinks[primary][1], 'volume_limit': 100, 'pulse_sink_name': sinks[primary][0]}}
        if secondary >= 0:
            outputs['secondary'] = {'alias': sinks[secondary][1], 'volume_limit': 100,
                                    'pulse_sink_name': sinks[secondary][0]}
        cfg = ctx.load_config()
        cfg.setn('volume', 'outputs', value=outputs)
        lauschkiste.cfghandler.write_yaml(cfg, str(ctx.config_path))
