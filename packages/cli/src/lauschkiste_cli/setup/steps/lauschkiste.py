"""Lauschkiste itself: plugins, the systemd user service, the RFID reader."""

from typing import List

import lauschkiste.contract.plugins as plugins
import lauschkiste.cfghandler
import lauschkiste.paths
from lauschkiste_cli import plugin
from lauschkiste_cli.environment import checkout, executable
from lauschkiste_cli.setup.base import Context, Question, Step
from lauschkiste_cli.setup.system import SetupError, StepSkipped

SERVICE = 'lauschkiste.service'


def wanted_plugins(ctx: Context) -> List[str]:
    names = [board['name'] for board in plugins.detected_boards(ctx.system.read)[:1]]
    if ctx.answer('mpd'):
        names.append('mpd')
    if ctx.answer('samba'):
        names.append('samba')
    return names


class PluginsStep(Step):
    name = 'plugins'
    title = 'Plugins'

    def _missing_extras(self, ctx) -> List[str]:
        """Extras of enabled (or to be enabled) plugins whose dependencies are missing, e.g. after
        the environment was recreated by an update."""
        names = dict.fromkeys([*ctx.enabled_plugins(), *wanted_plugins(ctx)])
        return [req for name in names for req in plugin.missing_extras(name)]

    def check(self, ctx):
        enabled = ctx.enabled_plugins()
        problems = [f"plugin '{name}' is not enabled" for name in wanted_plugins(ctx) if name not in enabled]
        problems += [f"dependencies {req} are not installed" for req in self._missing_extras(ctx)]
        return problems

    def apply(self, ctx):
        requirements = self._missing_extras(ctx)
        if requirements:
            plugin.install_requirements(requirements)
        enabled = ctx.enabled_plugins()
        plugin.add_to_config(ctx.config_path, [name for name in wanted_plugins(ctx) if name not in enabled])


class ServiceStep(Step):
    name = 'service'
    title = 'Lauschkiste service (systemd user unit)'
    questions = (
        Question('start_at_boot', 'Start Lauschkiste at boot, without anyone logging in?',
                 default=lambda ctx: ctx.system.is_raspberry_pi()),
    )
    UNIT_PATH = '~/.config/systemd/user/' + SERVICE

    def relevant(self, ctx):
        return ctx.system.which('systemctl') is not None

    def unit(self, ctx: Context) -> str:
        after = ['network.target', 'sound.target', 'pipewire-pulse.service']
        if 'mpd' in ctx.enabled_plugins():
            after.append('mpd.service')
        wants = [unit for unit in after if unit.endswith('.service')]
        workdir = checkout() or lauschkiste.paths.home()
        return (
            "[Unit]\n"
            "Description=Lauschkiste\n"
            "# Stopped before the sound server, so the shutdown sound can still play\n"
            f"After={' '.join(after)}\n"
            f"Wants={' '.join(wants)}\n"
            "\n"
            "[Service]\n"
            f"Environment={lauschkiste.paths.HOME_ENV}={lauschkiste.paths.home()}\n"
            f"WorkingDirectory={workdir}\n"
            f"ExecStart={executable('lauschkiste')}\n"
            "Restart=always\n"
            "\n"
            "[Install]\n"
            "WantedBy=default.target\n"
        )

    def _lingering(self, ctx) -> bool:
        return ctx.system.exists(f'/var/lib/systemd/linger/{ctx.system.user}')

    def check(self, ctx):
        problems = []
        if ctx.system.read(self.UNIT_PATH) != self.unit(ctx):
            problems.append(f'{self.UNIT_PATH} is missing or outdated')
        if not ctx.system.unit_enabled(SERVICE, user=True):
            problems.append(f'{SERVICE} is not enabled')
        if ctx.answer('start_at_boot') and not self._lingering(ctx):
            problems.append('user services do not start at boot (no lingering)')
        return problems

    def apply(self, ctx):
        system = ctx.system
        unit_changed = system.read(self.UNIT_PATH) != self.unit(ctx)
        system.write(self.UNIT_PATH, self.unit(ctx))
        system.run('systemctl', '--user', 'daemon-reload')
        was_running = system.unit_active(SERVICE, user=True)
        system.run('systemctl', '--user', 'enable', '--now', SERVICE)
        if was_running and unit_changed:
            system.run('systemctl', '--user', 'restart', SERVICE)
        if ctx.answer('start_at_boot') and not self._lingering(ctx):
            system.run('loginctl', 'enable-linger', system.user, root=True)


DEFAULT_PORT = 5556
PUBLIC_PORT = 80
HTTP_SOCKET = '/etc/systemd/system/lauschkiste-http.socket'
HTTP_SERVICE = '/etc/systemd/system/lauschkiste-http.service'
SOCKET_PROXY = '/usr/lib/systemd/systemd-socket-proxyd'


def web_port(ctx: Context) -> int:
    return int(ctx.load_config().getn('api', 'port', default=DEFAULT_PORT))


def public_port(ctx: Context) -> int:
    """The port the web app is reached at: 80 when the forwarding is set up, else its own."""
    return PUBLIC_PORT if ctx.system.exists(HTTP_SOCKET) else web_port(ctx)


class WebPortStep(Step):
    name = 'port'
    title = 'Web app on port 80'
    questions = (
        Question('port80', 'Serve the web app on port 80, so its address needs no ":5556"?',
                 default=lambda ctx: ctx.system.is_raspberry_pi(),
                 help='A systemd socket on port 80 forwards to the web app; Lauschkiste itself needs no extra rights'),
    )
    OLD_SYSCTL = '/etc/sysctl.d/60-lauschkiste-port.conf'
    SOCKET_UNIT = (
        '[Unit]\n'
        'Description=Lauschkiste web app on port 80\n'
        '\n'
        '[Socket]\n'
        f'ListenStream={PUBLIC_PORT}\n'
        '\n'
        '[Install]\n'
        'WantedBy=sockets.target\n'
    )

    def relevant(self, ctx):
        return ctx.system.which('systemctl') is not None

    def wanted(self, ctx):
        return bool(ctx.answer('port80'))

    def target(self, ctx) -> str:
        config = ctx.load_config()
        address = str(config.getn('api', 'bind_address', default='0.0.0.0'))
        host = '127.0.0.1' if address in ('', '0.0.0.0', '::') else address
        return f'{host}:{web_port(ctx)}'

    def service_unit(self, ctx) -> str:
        return (
            '[Unit]\n'
            'Description=Forwards port 80 to the Lauschkiste web app\n'
            'Requires=lauschkiste-http.socket\n'
            'After=lauschkiste-http.socket\n'
            '\n'
            '[Service]\n'
            f'ExecStart={SOCKET_PROXY} --exit-idle-time=10min {self.target(ctx)}\n'
            'DynamicUser=yes\n'
            'PrivateTmp=yes\n'
            'PrivateDevices=yes\n'
            'ProtectSystem=strict\n'
            'ProtectHome=yes\n'
            'NoNewPrivileges=yes\n'
            'RestrictAddressFamilies=AF_INET AF_INET6\n'
        )

    def check(self, ctx):
        system = ctx.system
        problems = []
        if not system.exists(SOCKET_PROXY):
            problems.append(f'{SOCKET_PROXY} is missing (part of systemd)')
        if system.read(HTTP_SOCKET) != self.SOCKET_UNIT:
            problems.append(f'{HTTP_SOCKET} is missing or outdated')
        if system.read(HTTP_SERVICE) != self.service_unit(ctx):
            problems.append(f'{HTTP_SERVICE} is missing or outdated')
        if not system.unit_enabled('lauschkiste-http.socket'):
            problems.append('lauschkiste-http.socket is not enabled')
        if web_port(ctx) == PUBLIC_PORT:
            problems.append(f'the web app itself uses port {PUBLIC_PORT}, which the forwarding needs')
        if system.exists(self.OLD_SYSCTL):
            problems.append('ports below 1024 are open to every program without root rights')
        return problems

    def apply(self, ctx):
        system = ctx.system
        if not system.exists(SOCKET_PROXY):
            raise SetupError(f'{SOCKET_PROXY} is missing; it belongs to systemd')
        if web_port(ctx) == PUBLIC_PORT:
            cfg = ctx.load_config()
            cfg.setn('api', 'port', value=DEFAULT_PORT)
            lauschkiste.cfghandler.write_yaml(cfg, str(ctx.config_path))
            if system.unit_active(SERVICE, user=True):
                system.run('systemctl', '--user', 'restart', SERVICE)
        if system.exists(self.OLD_SYSCTL):
            system.remove(self.OLD_SYSCTL, root=True)
            system.run('sysctl', '-w', 'net.ipv4.ip_unprivileged_port_start=1024', root=True, quiet=True)
        changed = (system.read(HTTP_SOCKET) != self.SOCKET_UNIT
                   or system.read(HTTP_SERVICE) != self.service_unit(ctx))
        system.write(HTTP_SOCKET, self.SOCKET_UNIT, root=True)
        system.write(HTTP_SERVICE, self.service_unit(ctx), root=True)
        system.run('systemctl', 'daemon-reload', root=True)
        system.run('systemctl', 'enable', '--now', 'lauschkiste-http.socket', root=True)
        if changed:
            system.run('systemctl', 'restart', 'lauschkiste-http.socket', root=True)
            system.run('systemctl', 'try-restart', 'lauschkiste-http.service', root=True)


class RfidStep(Step):
    name = 'rfid'
    title = 'RFID reader'
    questions = (
        Question('rfid', 'Configure an RFID reader now?', default=lambda ctx: ctx.system.is_raspberry_pi()),
    )

    def wanted(self, ctx):
        return bool(ctx.answer('rfid'))

    def check(self, ctx):
        problems = []
        if not (lauschkiste.paths.settings_dir() / 'rfid.yaml').exists():
            problems.append('no reader configuration (settings/rfid.yaml)')
        if not any(name.startswith('rfid_') for name in ctx.enabled_plugins()):
            problems.append('no reader driver plugin enabled')
        return problems

    def apply(self, ctx):
        if ctx.assume_yes:
            raise StepSkipped("the reader configuration is interactive; run 'lauschctl setup rfid' later")
        try:
            import lauschkiste_plugin_rfid_readers.configure as configure
        except ImportError as error:
            raise SetupError(f'the rfid-readers plugin package is not installed: {error}') from None
        config = configure.query_user_for_reader(dependency_install='query')
        configure.write_config(str(lauschkiste.paths.settings_dir() / 'rfid.yaml'), config, force_overwrite=True)
        drivers = sorted({f"rfid_{reader['module']}" for reader in config['rfid']['readers'].values()})
        plugin.add_to_config(ctx.config_path, drivers)
