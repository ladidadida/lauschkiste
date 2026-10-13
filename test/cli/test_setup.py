import pytest

import lauschkiste.common.paths
from lauschkiste_cli import plugin
from lauschkiste_cli.setup import run_setup
from lauschkiste_cli.setup.base import Answers, Context
from lauschkiste_cli.setup.system import System


class FakeSystem(System):
    def __init__(self, root, pi=False):
        super().__init__(root)
        self.use_sudo = False
        self.commands = []
        self.enabled = set()
        self.enabled_user = set()
        self.active = set()
        self.installed = {'build-essential', 'python3-dev', 'libffi-dev', 'alsa-utils', 'libportaudio2'}
        self.outputs = {
            ('ip', 'route', 'get', '8.8.8.8'): '8.8.8.8 via 192.168.1.1 dev wlan0 src 192.168.1.50 uid 1000',
            ('hostname',): 'jukebox',
        }
        (self.root / 'usr/bin').mkdir(parents=True)
        (self.root / 'usr/bin/apt-get').touch()
        (self.root / 'usr/lib/systemd').mkdir(parents=True)
        (self.root / 'usr/lib/systemd/systemd-socket-proxyd').touch()
        if pi:
            (self.root / 'usr/bin/raspi-config').touch()
            (self.root / 'proc/device-tree').mkdir(parents=True)
            (self.root / 'proc/device-tree/model').write_text('Raspberry Pi 4 Model B Rev 1.4')
            (self.root / 'boot/firmware').mkdir(parents=True)
            (self.root / 'boot/firmware/config.txt').write_text('dtparam=audio=on\n')
            (self.root / 'boot/firmware/cmdline.txt').write_text('console=tty1 root=PARTUUID=1234 rootwait\n')
            self.enabled |= {'bluetooth.service', 'apt-daily.timer', 'dhcpcd.service'}

    @property
    def user(self):
        return 'pi'

    def architecture(self):
        return 'arm64'

    def which(self, command):
        return f'/usr/bin/{command}'

    def run(self, *args, root=False, check=True, input=None, quiet=False):
        self.commands.append(args)
        if 'install' in args and 'apt-get' in args:
            self.installed |= {a for a in args[args.index('install') + 1:] if not a.startswith('-')}
        units = self.enabled_user if '--user' in args else self.enabled
        if args[0] == 'systemctl' and ('--now' in args or 'restart' in args or 'start' in args):
            self.active.add(args[-1])
        if args[0] == 'systemctl' and 'enable' in args:
            units |= set(a for a in args[args.index('enable') + 1:] if not a.startswith('-'))
        if args[0] == 'systemctl' and 'disable' in args:
            units -= set(args[args.index('disable') + 1:])
        if args[0] == 'loginctl':
            self.write(f'/var/lib/systemd/linger/{args[-1]}', '')
        if args[0] == 'smbpasswd':
            self.outputs[('pdbedit', '-L')] = f'{args[-1]}:1000:'

    def output(self, *args):
        return self.outputs.get(tuple(args), '')

    def unit_active(self, unit, user=False):
        return unit in self.active

    def unit_enabled(self, unit, user=False):
        return unit in (self.enabled_user if user else self.enabled)

    def missing_packages(self, packages):
        return [p for p in packages if p not in self.installed]


@pytest.fixture
def home(tmp_path):
    lauschkiste.common.paths.set_home(tmp_path / 'home')
    yield tmp_path / 'home'
    lauschkiste.common.paths.set_home(None)


@pytest.fixture
def extras(monkeypatch):
    """Records installed extras; an extra counts as missing until it has been installed here."""
    installed = []
    monkeypatch.setattr(plugin, 'install_requirements', installed.extend)
    monkeypatch.setattr(plugin, 'missing_extras',
                        lambda name: [req for req in plugin.plugin_extras(name) if req not in installed])
    return installed


def setup_run(system, home, names=None, answers=None, check_only=False):
    ctx = Context(system=system, config_path=home / 'settings' / 'lauschkiste.yaml', assume_yes=True)
    store = Answers(home / 'settings' / 'setup.yaml')
    if answers is not None:
        store.save(answers)
    return run_setup(names, ctx, store, check_only=check_only), ctx


def test_pc_setup_installs_packages_and_service(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root')
    failed, ctx = setup_run(system, home)
    assert failed == 0
    assert any('install' in c and 'espeak' in c for c in system.commands)
    unit = system.read('~/.config/systemd/user/lauschkiste.service')
    assert f'Environment=LAUSCHKISTE_HOME={home}' in unit
    assert 'lauschkiste.service' in system.enabled_user
    assert not system.exists('/var/lib/systemd/linger/pi')
    assert ctx.enabled_plugins() == {'device_pc_test': {}}
    assert extras == []
    assert not system.exists('/etc/systemd/system/lauschkiste-http.socket')


def test_network_stays_on_dhcp_by_default(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    assert setup_run(system, home)[0] == 0
    assert 'static ip_address' not in (system.read('/etc/dhcpcd.conf') or '')
    assert not any('nmcli' in command for command in system.commands)


def test_second_run_changes_nothing(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    assert setup_run(system, home)[0] == 0
    system.commands.clear()
    assert setup_run(system, home)[0] == 0
    assert system.commands == []


def test_pi_setup(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    system.outputs[('pdbedit', '-L')] = 'pi:1000:'
    failed, ctx = setup_run(system, home, answers={'samba': True, 'optimize_boot': True, 'disable_bluetooth': True})
    assert failed == 0
    assert {'device_raspberry_pi', 'samba'} <= set(ctx.enabled_plugins())
    assert system.exists('/var/lib/systemd/linger/pi')
    assert 'disable_splash=1' in system.read('/boot/firmware/config.txt')
    cmdline = system.read('/boot/firmware/cmdline.txt')
    assert cmdline.startswith('console=tty1 root=PARTUUID=1234 rootwait ')
    assert 'ipv6.disable' not in cmdline and cmdline.count('quiet') == 1
    assert any('command line changed' in note for note in ctx.notes)
    assert 'apt-daily.timer' in system.enabled
    assert 'bluetooth.service' not in system.enabled
    assert 'ListenStream=80' in system.read('/etc/systemd/system/lauschkiste-http.socket')
    forwarding = system.read('/etc/systemd/system/lauschkiste-http.service')
    assert 'systemd-socket-proxyd --exit-idle-time=10min 127.0.0.1:5556' in forwarding
    assert 'lauschkiste-http.socket' in system.enabled
    assert ctx.load_config().getn('api', 'port', default=5556) == 5556
    assert not system.exists('/etc/sysctl.d/60-lauschkiste-port.conf')
    welcome = system.read('/etc/update-motd.d/99-lauschkiste-welcome')
    assert 'port=":80"' in welcome and '5556' not in welcome
    assert not system.exists('/etc/dhcpcd.conf')
    smb = system.read('/etc/samba/smb.conf')
    assert f'path={home / "library"}\n' in smb and smb.count('## Lauschkiste Samba Config') == 1
    assert 'force user=pi' in smb and '0777' not in smb
    assert system.exists('/etc/update-motd.d/99-lauschkiste-welcome')


def test_answers_are_stored_without_secrets(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    setup_run(system, home, answers={'samba': True})
    stored = Answers(home / 'settings' / 'setup.yaml').load()
    assert stored['samba'] is True
    assert stored['optimize_boot'] is False and 'static_ip' not in stored


def test_check_changes_nothing(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    failed, _ = setup_run(system, home, check_only=True)
    assert failed > 0
    assert system.commands == []
    assert not (home / 'settings' / 'setup.yaml').exists()
    assert 'audio=on' in system.read('/boot/firmware/config.txt')


def test_single_step_and_irrelevant_steps(tmp_path, home, extras, capsys):
    system = FakeSystem(tmp_path / 'root')
    failed, _ = setup_run(system, home, names=['boot', 'service'])
    assert failed == 0
    assert "Skipping 'boot'" in capsys.readouterr().out
    assert not any('apt-get' in c for c in system.commands)


def test_hotspot(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    system.enabled.add('NetworkManager.service')
    system.outputs[('iw', 'dev')] = 'phy#0\n\tInterface wlan0\n'
    failed, ctx = setup_run(system, home, answers={'autohotspot': True})
    assert failed == 0
    script = system.read('/usr/bin/autohotspot')
    assert "ap_ssid='Lauschkiste_jukebox'" in script and "wdev0='wlan0'" in script
    assert 'autohotspot.timer' in system.enabled
    assert not system.exists('/etc/dhcpcd.conf')


def test_audio_is_skipped_unattended_and_writes_outputs_interactively(tmp_path, home, extras, monkeypatch):
    from lauschkiste_cli.setup.steps import extras as extras_steps
    system = FakeSystem(tmp_path / 'root')
    failed, ctx = setup_run(system, home, names=['audio'], answers={'audio': True})
    assert failed == 0

    monkeypatch.setattr(extras_steps.AudioStep, '_sinks',
                        lambda self, ctx: [('alsa_output.analog', 'Speakers'), ('bluez_sink.x', 'Headset')])
    answers = iter([0, 1])
    monkeypatch.setattr(extras_steps.typer, 'prompt', lambda *a, **k: next(answers))
    ctx.assume_yes = False
    extras_steps.AudioStep().apply(ctx)
    outputs = ctx.load_config().getn('volume', 'outputs')
    assert outputs['primary']['pulse_sink_name'] == 'alsa_output.analog'
    assert outputs['secondary']['alias'] == 'Headset'
    assert extras_steps.AudioStep().check(ctx) == []


def _board_settings(home, settings, rfid=None):
    import lauschkiste.common.statefile as statefile
    path = home / 'settings' / 'lauschkiste.yaml'
    config = statefile.read_yaml(path) if path.exists() else {}
    config['plugins'] = {'device_raspberry_pi': settings}
    statefile.write_yaml(path, config)
    if rfid is not None:
        statefile.write_yaml(home / 'settings' / 'rfid.yaml', rfid)


def test_boot_configuration_follows_the_board_settings(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    system.write('/boot/firmware/config.txt', 'dtparam=audio=on\ndtoverlay=hifiberry-dac\n[all]\n')
    _board_settings(home, {'sound_card': 'max98357a'},
                    {'rfid': {'readers': {'read_00': {'module': 'rc522_spi', 'config': {}}}}})
    failed, _ = setup_run(system, home, names=['raspi'])
    assert failed == 0
    config = system.read('/boot/firmware/config.txt')
    assert 'dtoverlay=max98357a' in config and 'hifiberry-dac' not in config
    assert 'audio=off' in config and 'dtparam=spi=on' in config and '[all]' in config
    assert system.read('/boot/firmware/config.txt.backup').startswith('dtparam=audio=on')


def test_boot_configuration_unchanged_when_nothing_is_wanted(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    system.write('/boot/firmware/config.txt', 'dtparam=audio=on\n')
    _board_settings(home, {})
    failed, _ = setup_run(system, home, names=['raspi'])
    assert failed == 0
    assert not system.exists('/boot/firmware/config.txt.backup')


@pytest.mark.parametrize('architecture, expected', [('armv6', True), ('armv7', True), ('arm64', False)])
def test_ffmpeg_libraries_for_piwheels(tmp_path, home, extras, monkeypatch, architecture, expected):
    from lauschkiste_cli.setup.steps.system import PackagesStep
    system = FakeSystem(tmp_path / 'root', pi=True)
    monkeypatch.setattr(system, 'architecture', lambda: architecture)
    ctx = Context(system=system, config_path=home / 'settings' / 'lauschkiste.yaml')
    assert ('ffmpeg' in PackagesStep().packages(ctx)) is expected


def test_service_is_started_and_restarted_after_a_unit_change(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root')
    setup_run(system, home, names=['service'])
    assert 'lauschkiste.service' in system.active
    assert ('systemctl', '--user', 'enable', '--now', 'lauschkiste.service') in system.commands
    assert not any('restart' in c for c in system.commands)

    system.commands.clear()
    system.write('~/.config/systemd/user/lauschkiste.service', '[Unit]\nDescription=old\n')
    setup_run(system, home, names=['service'])
    assert ('systemctl', '--user', 'restart', 'lauschkiste.service') in system.commands


def test_missing_extras_of_enabled_plugins_are_reinstalled(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root')
    plugin.add_to_config(home / 'settings' / 'lauschkiste.yaml', ['rfid_rc522_spi'])
    failed, _ = setup_run(system, home, names=['plugins'])
    assert failed == 0
    assert extras == ['lauschkiste-plugins[rc522-spi]']


def test_samba_asks_for_a_password_and_never_sets_a_default(tmp_path, home, extras, monkeypatch):
    from lauschkiste_cli.setup.steps import extras as extras_steps
    system = FakeSystem(tmp_path / 'root')
    failed, _ = setup_run(system, home, names=['samba'], answers={'samba': True})
    assert failed == 0
    assert not any(c[0] == 'smbpasswd' for c in system.commands)

    passwords = iter(['short', 'long enough'])
    monkeypatch.setattr(extras_steps.typer, 'prompt', lambda *a, **k: next(passwords))
    ctx = Context(system=system, config_path=home / 'settings' / 'lauschkiste.yaml', answers={'samba': True})
    extras_steps.SambaStep().apply(ctx)
    smbpasswd = [c for c in system.commands if c[0] == 'smbpasswd']
    assert smbpasswd == [('smbpasswd', '-s', '-a', 'pi')]
    assert extras_steps.SambaStep().check(ctx) == []


def test_replace_block_keeps_the_rest_of_the_file(tmp_path):
    system = FakeSystem(tmp_path / 'root')
    system.write('/etc/x.conf', '[global]\n  a=1\n\n## Lauschkiste Samba Config\n[lauschkiste]\n'
                                 '  path=/old\n  x=1\n\n[other]\n  b=2\n')
    system.replace_block('/etc/x.conf', '## Lauschkiste Samba Config', '[lauschkiste]\n  path=/new')
    assert system.read('/etc/x.conf') == ('[global]\n  a=1\n\n## Lauschkiste Samba Config\n[lauschkiste]\n'
                                          '  path=/new\n\n[other]\n  b=2\n')
    assert system.read_block('/etc/x.conf', '## Lauschkiste Samba Config') == (
        '## Lauschkiste Samba Config\n[lauschkiste]\n  path=/new')


def test_port_step_replaces_the_old_sysctl_setting_and_moves_the_web_app_off_port_80(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    system.write('/etc/sysctl.d/60-lauschkiste-port.conf', 'net.ipv4.ip_unprivileged_port_start = 80\n')
    home.mkdir(parents=True, exist_ok=True)
    (home / 'settings').mkdir(exist_ok=True)
    (home / 'settings' / 'lauschkiste.yaml').write_text('api:\n  port: 80\n  bind_address: 192.168.1.50\n')
    failed, ctx = setup_run(system, home, names=['port'])
    assert failed == 0
    assert not system.exists('/etc/sysctl.d/60-lauschkiste-port.conf')
    assert ('sysctl', '-w', 'net.ipv4.ip_unprivileged_port_start=1024') in system.commands
    assert ctx.load_config().getn('api', 'port') == 5556
    assert '192.168.1.50:5556' in system.read('/etc/systemd/system/lauschkiste-http.service')
    assert setup_run(system, home, names=['port'], check_only=True)[0] == 0


def test_port_step_needs_the_socket_proxy(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    (system.root / 'usr/lib/systemd/systemd-socket-proxyd').unlink()
    assert setup_run(system, home, names=['port'])[0] == 1


def test_hardware_step_sets_the_sound_card_of_the_device(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    answers = {'hw_sound_card': 'max98357a'}
    failed, ctx = setup_run(system, home, names=['device', 'hardware'], answers=answers)
    assert failed == 0
    assert ctx.enabled_plugins()['device_raspberry_pi']['sound_card'] == 'max98357a'
    failed, _ = setup_run(system, home, names=['device', 'hardware'], answers=answers, check_only=True)
    assert failed == 0


def test_peripherals_are_proposed_and_enabled_with_their_options(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    answers = {'peripheral_power_button': True, 'peripheral_battery': True, 'opt_battery_driver': 'ina219',
               'peripheral_phat_beat': False}
    names = ['device', 'peripherals', 'peripheral_options']
    failed, ctx = setup_run(system, home, names=names, answers=answers)
    assert failed == 0
    plugins = ctx.enabled_plugins()
    assert plugins['battery']['driver'] == 'ina219' and 'power_button' in plugins and 'phat_beat' not in plugins
    failed, _ = setup_run(system, home, names=names, answers=answers, check_only=True)
    assert failed == 0


def test_a_peripheral_that_is_no_longer_chosen_is_switched_off(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    names = ['device', 'peripherals']
    setup_run(system, home, names=names, answers={'peripheral_phat_beat': True})
    assert 'phat_beat' in setup_run(system, home, names=names, check_only=True)[1].enabled_plugins()
    failed, ctx = setup_run(system, home, names=names, answers={'peripheral_phat_beat': False})
    assert failed == 0 and 'phat_beat' not in ctx.enabled_plugins()


def test_peripherals_that_need_what_the_device_lacks_are_not_proposed(tmp_path, home, extras):
    from lauschkiste_cli.setup.steps.peripherals import PeripheralsStep
    ctx = Context(system=FakeSystem(tmp_path / 'root'), config_path=home / 'settings' / 'lauschkiste.yaml')
    assert ctx.device_name() == 'device_pc_test'
    assert PeripheralsStep().questions_for(ctx) == ()
    pi = Context(system=FakeSystem(tmp_path / 'pi', pi=True), config_path=home / 'settings' / 'lauschkiste.yaml')
    assert {q.key for q in PeripheralsStep().questions_for(pi)} >= {'peripheral_battery', 'peripheral_phat_beat'}


def test_hardware_step_is_skipped_off_the_raspberry_pi(tmp_path, home, extras):
    failed, ctx = setup_run(FakeSystem(tmp_path / 'root'), home, names=['hardware'])
    assert failed == 0 and 'device_raspberry_pi' not in ctx.enabled_plugins()


def test_reboot_note_after_a_changed_boot_configuration(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    _board_settings(home, {'sound_card': 'max98357a'}, {})
    _, ctx = setup_run(system, home, names=['raspi'])
    assert any('Reboot' in note for note in ctx.notes)


def test_a_choice_is_picked_by_number_or_value(monkeypatch):
    from lauschkiste_cli.setup.base import Question, ask
    question = Question('card', 'Which?', kind='choice', choices=(('none', 'Nothing'), ('a', 'A'), ('b', 'B')))
    ctx = Context(system=None, config_path=None)
    for typed, expected in (('3', 'b'), ('a', 'a'), ('', 'none')):
        monkeypatch.setattr('typer.prompt', lambda *a, _t=typed, **k: _t or k['default'])
        assert ask(question, ctx, {}, assume_yes=False) == expected
    monkeypatch.setattr('typer.prompt', lambda *a, **k: k['default'])
    assert ask(question, ctx, {'card': 'b'}, assume_yes=False) == 'b'


@pytest.mark.parametrize('text, expected', [
    ('lauschkiste-plugin-foo', 'lauschkiste-plugin-foo'),
    ('lauschkiste-plugin-foo==1.2', 'lauschkiste-plugin-foo==1.2'),
    ('github:someone/the-plugin', 'git+https://github.com/someone/the-plugin'),
    ('github:someone/the-plugin@v1.2', 'git+https://github.com/someone/the-plugin@v1.2'),
    ('https://example.org/foo-1.0-py3-none-any.whl', 'https://example.org/foo-1.0-py3-none-any.whl'),
])
def test_plugin_sources_are_translated(text, expected):
    from lauschkiste_cli.setup.steps.extra_plugins import parse_spec
    assert parse_spec(text) == expected


@pytest.mark.parametrize('text', ['--index-url=https://evil.example', '-r', 'not a requirement!', 'github:only-owner'])
def test_plugin_sources_reject_options_and_nonsense(text):
    from lauschkiste_cli.setup.steps.extra_plugins import parse_spec
    with pytest.raises(ValueError):
        parse_spec(text)


def test_extra_plugins_are_installed_enabled_and_remembered(tmp_path, home, extras, monkeypatch):
    import lauschkiste.contract.plugins as contract_plugins
    system = FakeSystem(tmp_path / 'root')
    available = dict(contract_plugins.installed())
    calls = []

    def install(requirements):
        calls.extend(requirements)
        if requirements == ['git+https://github.com/someone/clock']:
            available['clock'] = object()

    monkeypatch.setattr(plugin, 'install_requirements', install)
    monkeypatch.setattr(contract_plugins, 'installed', lambda: dict(available))
    monkeypatch.setattr(contract_plugins, 'why_not_enable', lambda cfg, name: None)
    monkeypatch.setattr(plugin, 'plugin_extras', lambda name: [])
    answers = {'extra_plugins': 'github:someone/clock'}
    failed, ctx = setup_run(system, home, names=['extra_plugins'], answers=answers)
    assert failed == 0
    assert calls == ['git+https://github.com/someone/clock']
    assert 'clock' in ctx.enabled_plugins()
    assert (home / 'settings' / 'extra_plugins.json').exists()
    assert 'git' in system.installed
    failed, _ = setup_run(system, home, names=['extra_plugins'], answers=answers)
    assert failed == 0 and calls == ['git+https://github.com/someone/clock']


def test_without_extra_plugins_nothing_happens(tmp_path, home, extras):
    failed, ctx = setup_run(FakeSystem(tmp_path / 'root'), home, names=['extra_plugins'])
    assert failed == 0 and not (home / 'settings' / 'extra_plugins.json').exists()


@pytest.mark.parametrize('codename, architecture, expected', [
    ('trixie', 'arm64', 'chromium'), ('bookworm', 'arm64', 'chromium-browser'), ('bookworm', 'x86_64', 'chromium'),
    (None, 'arm64', 'chromium'),
])
def test_chromium_package_follows_the_debian_release(tmp_path, home, extras, codename, architecture, expected):
    from lauschkiste_cli.setup.steps.extras import KioskStep
    system = FakeSystem(tmp_path / 'root')
    system.architecture = lambda: architecture
    if codename:
        system.write('/etc/os-release', f'VERSION_CODENAME={codename}\n')
    ctx = Context(system=system, config_path=home / 'settings' / 'lauschkiste.yaml')
    step = KioskStep()
    assert step._chromium(ctx) == expected
    assert expected in step.packages(ctx)
    assert step._update_check_file(ctx).startswith('/etc/chromium.d/' if expected == 'chromium' else '/etc/chromium-browser')


def test_a_quiet_boot_is_an_explicit_choice_and_never_touches_the_network(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    failed, ctx = setup_run(system, home, names=['boot'], answers={'optimize_boot': True})
    assert failed == 0
    cmdline = system.read('/boot/firmware/cmdline.txt')
    assert 'quiet' in cmdline and 'ipv6' not in cmdline and 'noatime' not in cmdline
    assert 'bluetooth.service' in system.enabled and 'apt-daily.timer' in system.enabled
    assert not any('nmcli' in command or 'dhcpcd' in str(command) for command in system.commands)


def test_kiosk_step_repairs_an_outdated_chromium_command(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    system.write('/etc/os-release', 'VERSION_CODENAME=trixie\n')
    system.write('/etc/xdg/openbox/autostart', 'keep\n\n## Lauschkiste Kiosk Mode\nxset s off\n'
                 'chromium-browser http://localhost:5556 --kiosk\n\nother\n')
    system.write('~/.bashrc', 'before\n')
    system.write('/etc/systemd/system/getty@tty1.service.d/autologin.conf', '')
    answers = {'kiosk': True}
    failed, _ = setup_run(system, home, names=['kiosk'], answers=answers)
    assert failed == 0
    autostart = system.read('/etc/xdg/openbox/autostart')
    assert 'chromium http://localhost:5556' in autostart and 'chromium-browser' not in autostart
    assert autostart.count('## Lauschkiste Kiosk Mode') == 1 and autostart.startswith('keep\n') and 'other' in autostart
    assert 'xset -dpms' in autostart and 'dpms 0 0' not in autostart
    assert system.read('~/.bashrc').count('startx') == 1
    failed, _ = setup_run(system, home, names=['kiosk'], answers=answers, check_only=True)
    assert failed == 0


def test_hardware_step_offers_the_detected_sound_card(tmp_path, home, extras):
    from lauschkiste_plugin_device_raspberry_pi.setup import HardwareStep
    system = FakeSystem(tmp_path / 'root', pi=True)
    ctx = Context(system=system, config_path=home / 'settings' / 'lauschkiste.yaml')
    question = {q.key: q for q in HardwareStep.questions}['hw_sound_card']
    assert question.default_for(ctx) == 'none' and question.help(ctx) == ''
    system.write('/proc/device-tree/hat/vendor', 'HiFiBerry\x00')
    system.write('/proc/device-tree/hat/product', 'DAC+\x00')
    assert question.default_for(ctx) == 'hifiberry-dacplus'
    assert 'HiFiBerry DAC+' in question.help(ctx)
    system.write('/proc/device-tree/hat/product', 'Something else\x00')
    assert question.default_for(ctx) == 'none' and 'not a sound card' in question.help(ctx)


def test_audio_output_label_names_the_sound_card():
    from collections import namedtuple
    from lauschkiste_cli.setup.steps.extras import AudioStep
    hat = namedtuple('Hat', 'vendor label')('HiFiBerry', 'HiFiBerry DAC+')
    label = AudioStep._label
    assert label('Built-in Audio Stereo', 'snd_rpi_hifiberry_dacplus', hat) == 'HiFiBerry DAC+'
    assert label('Built-in Audio Stereo', 'snd_rpi_hifiberry_dacplus', None) == 'hifiberry dacplus'
    assert label('Built-in Audio Stereo', 'bcm2835 Headphones', None) == 'bcm2835 Headphones'
    assert label('Built-in Audio Stereo', '', None) == 'Built-in Audio Stereo'
    assert label('Speakers', 'snd_rpi_hifiberry_dacplus', hat) == 'Speakers'


def test_a_pc_is_offered_none_of_the_system_changes(tmp_path, home, extras, capsys):
    system = FakeSystem(tmp_path / 'root')
    failed, ctx = setup_run(system, home, answers={'port80': True, 'samba': True, 'kiosk': True, 'autohotspot': True,
                                                   'optimize_boot': True, 'upgrade_os': True})
    assert failed == 0
    assert ctx.device_name() == 'device_pc_test' and not ctx.provides('system_setup')
    assert 'samba' not in ctx.enabled_plugins()
    assert not system.exists('/etc/systemd/system/lauschkiste-http.socket')
    assert not system.exists('/etc/xdg/openbox/autostart')
    assert not system.exists('/etc/update-motd.d/99-lauschkiste-welcome')
    assert not any('full-upgrade' in command for command in system.commands)
    assert 'upgrade_os' not in ctx.answers and 'kiosk' not in ctx.answers


def test_a_raspberry_pi_gets_the_pi_device_and_its_steps(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    failed, ctx = setup_run(system, home)
    assert failed == 0
    assert ctx.device_name() == 'device_raspberry_pi' and ctx.provides('system_setup', 'boot_config', 'screen')
    assert 'device_raspberry_pi' in ctx.enabled_plugins() and 'device_pc_test' not in ctx.enabled_plugins()


def test_choosing_none_changes_nothing_on_a_pi(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    failed, ctx = setup_run(system, home, answers={'device': 'none', 'optimize_boot': True})
    assert failed == 0
    assert ctx.device_name() is None and not ctx.provides('system_setup')
    assert not any(name.startswith('device_') for name in ctx.enabled_plugins())
    assert 'splash' not in system.read('/boot/firmware/cmdline.txt')


def test_another_device_replaces_the_enabled_one(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    setup_run(system, home)
    failed, ctx = setup_run(system, home, answers={'device': 'device_pc_test'})
    assert failed == 0
    assert set(name for name in ctx.enabled_plugins() if name.startswith('device_')) == {'device_pc_test'}


def test_a_device_plugin_of_my_own(tmp_path, home, extras, monkeypatch):
    from lauschkiste.contract import Plugin
    from lauschkiste_cli.setup.steps import device, extra_plugins

    class Mine(Plugin):
        name = 'device_mine'
        provides = ('device', 'system_setup')

    monkeypatch.setattr(device, '_device_classes', lambda: {'device_mine': Mine})
    monkeypatch.setattr(extra_plugins, '_state', lambda: {'git+https://github.com/me/mine': ['device_mine']})
    monkeypatch.setattr(extra_plugins, '_state_path', lambda: tmp_path / 'state.json')
    system = FakeSystem(tmp_path / 'root')
    failed, ctx = setup_run(system, home, names=['device'],
                            answers={'device': 'own', 'device_plugin': 'github:me/mine'})
    assert ctx.device_name() == 'device_mine' and ctx.provides('system_setup')


def test_a_pc_as_a_box_of_its_own_may_be_set_up_but_has_no_boot_configuration(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root')
    system.write('/etc/os-release', 'VERSION_CODENAME=trixie\n')
    answers = {'device': 'device_pc_box', 'port80': True, 'kiosk': True, 'optimize_boot': True}
    failed, ctx = setup_run(system, home, answers=answers)
    assert failed == 0
    assert ctx.provides('system_setup', 'autologin', 'screen') and not ctx.provides('boot_config')
    assert system.exists('/etc/systemd/system/lauschkiste-http.socket')
    assert 'chromium' in system.read('/etc/xdg/openbox/autostart')
    assert '--autologin pi' in system.read('/etc/systemd/system/getty@tty1.service.d/autologin.conf')
    assert 'optimize_boot' not in ctx.answers
    assert 'device_pc_box' in ctx.enabled_plugins()


def test_a_peripheral_from_another_source_is_proposed_not_enabled(tmp_path, home, extras, monkeypatch):
    from lauschkiste.contract import Plugin
    from lauschkiste_cli.setup.steps import extra_plugins, peripherals

    class Knob(Plugin):
        """A rotary knob from a third party."""
        name = 'knob'
        title = 'Third party knob'
        setup_kind = 'peripheral'

    class Other(Plugin):
        name = 'other'

    monkeypatch.setattr(extra_plugins, '_is_peripheral', lambda name: name == 'knob')
    monkeypatch.setattr(peripherals, 'candidates', lambda ctx: {'knob': Knob})
    monkeypatch.setattr(extra_plugins, '_state', lambda: {'knob-pkg': ['knob']})
    monkeypatch.setattr(extra_plugins, '_state_path', lambda: tmp_path / 'state.json')
    system = FakeSystem(tmp_path / 'root')
    ctx = Context(system=system, config_path=home / 'settings' / 'lauschkiste.yaml')
    questions = peripherals.PeripheralsStep().questions_for(ctx)
    assert [(q.key, q.default, q.help) for q in questions] == [('peripheral_knob', True, 'A rotary knob from a third party.')]
    assert 'knob' not in ctx.enabled_plugins()


def test_the_device_plugin_brings_its_own_steps(tmp_path, home, extras, monkeypatch):
    from lauschkiste.contract import Plugin
    from lauschkiste_cli.setup.base import Question, Step
    from lauschkiste_cli.setup.steps import device

    class Tune(Step):
        name = 'tune'
        title = 'Tuning of my device'
        questions = (Question('tune', 'Tune it?', default=True),)
        applied = []

        def wanted(self, ctx):
            return bool(ctx.answer('tune'))

        def check(self, ctx):
            return [] if self.applied else ['not tuned']

        def apply(self, ctx):
            self.applied.append(ctx.answer('tune'))

    class Mine(Plugin):
        name = 'device_mine'
        provides = ('device', 'system_setup')

        @classmethod
        def setup_steps(cls):
            return [Tune()]

    monkeypatch.setattr(device, '_device_classes', lambda: {'device_mine': Mine})
    system = FakeSystem(tmp_path / 'root')
    failed, ctx = setup_run(system, home, answers={'device': 'device_mine'})
    assert failed == 0 and Tune.applied == [True] and ctx.answers['tune'] is True


def test_steps_of_another_device_are_not_offered(tmp_path, home, extras, capsys):
    system = FakeSystem(tmp_path / 'root')
    failed, ctx = setup_run(system, home, answers={'device': 'device_pc_box'}, names=['raspi', 'hardware'])
    assert failed == 0 and 'hw_sound_card' not in ctx.answers
    out = capsys.readouterr().out
    assert "Skipping 'raspi'" in out and "Skipping 'hardware'" in out
