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


def web_port(ctx: Context) -> int:
    return int(ctx.load_config().getn('api', 'port', default=DEFAULT_PORT))


class WebPortStep(Step):
    name = 'port'
    title = 'Web app on port 80'
    questions = (
        Question('port80', 'Serve the web app on port 80, so its address needs no ":5556"?',
                 default=lambda ctx: ctx.system.is_raspberry_pi(),
                 help='Lets programs without root rights use ports from 80 up (net.ipv4.ip_unprivileged_port_start)'),
    )
    SYSCTL = '/etc/sysctl.d/60-lauschkiste-port.conf'
    CONTENT = '# Lauschkiste serves its web app on port 80 without root rights\nnet.ipv4.ip_unprivileged_port_start = 80\n'

    def wanted(self, ctx):
        return bool(ctx.answer('port80'))

    def check(self, ctx):
        problems = []
        if ctx.system.read(self.SYSCTL) != self.CONTENT:
            problems.append('programs without root rights may not use port 80')
        if web_port(ctx) != 80:
            problems.append('the web app does not use port 80')
        return problems

    def apply(self, ctx):
        system = ctx.system
        system.write(self.SYSCTL, self.CONTENT, root=True)
        system.run('sysctl', '-p', self.SYSCTL, root=True, quiet=True)
        if web_port(ctx) != 80:
            cfg = ctx.load_config()
            cfg.setn('api', 'port', value=80)
            lauschkiste.cfghandler.write_yaml(cfg, str(ctx.config_path))
            if system.unit_active(SERVICE, user=True):
                system.run('systemctl', '--user', 'restart', SERVICE)


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
