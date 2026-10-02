import pytest

import lauschkiste.paths
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
        if pi:
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
    lauschkiste.paths.set_home(tmp_path / 'home')
    yield tmp_path / 'home'
    lauschkiste.paths.set_home(None)


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
    assert ctx.enabled_plugins() == {}
    assert extras == []


def test_second_run_changes_nothing(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    assert setup_run(system, home)[0] == 0
    system.commands.clear()
    assert setup_run(system, home)[0] == 0
    assert system.commands == []


def test_pi_setup(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    system.outputs[('pdbedit', '-L')] = 'pi:1000:'
    failed, ctx = setup_run(system, home, answers={'disable_onboard_audio': True, 'samba': True})
    assert failed == 0
    assert 'raspberry_pi' in ctx.enabled_plugins()
    assert extras == ['lauschkiste-plugin-raspberry-pi[gpio]']
    assert system.exists('/var/lib/systemd/linger/pi')
    assert 'audio=off' in system.read('/boot/firmware/config.txt')
    assert 'disable_splash=1' in system.read('/boot/firmware/config.txt')
    cmdline = system.read('/boot/firmware/cmdline.txt')
    assert cmdline.startswith('console=tty1 root=PARTUUID=1234 rootwait ')
    assert 'ipv6.disable=1' in cmdline and cmdline.count('quiet') == 1
    assert 'bluetooth.service' not in system.enabled
    assert 'static ip_address=192.168.1.50/24' in system.read('/etc/dhcpcd.conf')
    smb = system.read('/etc/samba/smb.conf')
    assert f'path={home / "audiofolders"}\n' in smb and smb.count('## Lauschkiste Samba Config') == 1
    assert 'force user=pi' in smb and '0777' not in smb
    assert system.exists('/etc/update-motd.d/99-lauschkiste-welcome')


def test_answers_are_stored_without_secrets(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    setup_run(system, home, answers={'samba': True})
    stored = Answers(home / 'settings' / 'setup.yaml').load()
    assert stored['samba'] is True
    assert stored['optimize_boot'] is True


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


def test_mpd_and_hotspot(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    system.enabled.add('NetworkManager.service')
    system.outputs[('iw', 'dev')] = 'phy#0\n\tInterface wlan0\n'
    failed, ctx = setup_run(system, home, answers={'mpd': True, 'autohotspot': True})
    assert failed == 0
    assert 'mpd' in ctx.enabled_plugins()
    assert 'mpd.service' in system.read('~/.config/systemd/user/lauschkiste.service')
    assert str(home / 'audiofolders') in system.read('~/.config/mpd/mpd.conf')
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
                        lambda self: [('alsa_output.analog', 'Speakers'), ('bluez_sink.x', 'Headset')])
    answers = iter([0, 1])
    monkeypatch.setattr(extras_steps.typer, 'prompt', lambda *a, **k: next(answers))
    ctx.assume_yes = False
    extras_steps.AudioStep().apply(ctx)
    outputs = ctx.load_config().getn('volume', 'outputs')
    assert outputs['primary']['pulse_sink_name'] == 'alsa_output.analog'
    assert outputs['secondary']['alias'] == 'Headset'
    assert extras_steps.AudioStep().check(ctx) == []


def test_hifiberry_replaces_other_overlays(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    system.write('/boot/firmware/config.txt', 'dtparam=audio=on\ndtoverlay=hifiberry-dac\n[all]\n')
    failed, _ = setup_run(system, home, names=['raspi'], answers={'sound_card': 'hifiberry-amp3'})
    assert failed == 0
    config = system.read('/boot/firmware/config.txt')
    assert 'dtoverlay=hifiberry-amp3' in config and 'hifiberry-dac' not in config
    assert 'audio=off' in config and '[all]' in config
    assert system.read('/boot/firmware/config.txt.backup').startswith('dtparam=audio=on')


def test_existing_sound_card_is_the_default(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    system.write('/boot/firmware/config.txt', 'dtparam=audio=off\ndtoverlay=hifiberry-dacplus\n')
    failed, ctx = setup_run(system, home, names=['raspi'])
    assert failed == 0
    assert ctx.answers['sound_card'] == 'hifiberry-dacplus'
    assert not system.exists('/boot/firmware/config.txt.backup')


@pytest.mark.parametrize('architecture, expected', [('armv6', True), ('armv7', True), ('arm64', False)])
def test_ffmpeg_libraries_for_piwheels(tmp_path, home, extras, monkeypatch, architecture, expected):
    from lauschkiste_cli.setup.steps.system import PackagesStep
    system = FakeSystem(tmp_path / 'root', pi=True)
    monkeypatch.setattr(system, 'architecture', lambda: architecture)
    ctx = Context(system=system, config_path=home / 'settings' / 'lauschkiste.yaml')
    assert ('ffmpeg' in PackagesStep().packages(ctx)) is expected


def test_blocks_and_service_from_before_the_renaming(tmp_path, home, extras):
    system = FakeSystem(tmp_path / 'root', pi=True)
    system.write('/boot/firmware/config.txt', 'dtparam=audio=on\n\n## Jukebox Boot Config\ndisable_splash=1\n')
    system.write('/etc/samba/smb.conf', f'[global]\n\n## Jukebox Samba Config\n[jukebox]\n  path={home}\n')
    system.outputs[('pdbedit', '-L')] = 'pi:1000:'
    system.write('~/.config/systemd/user/jukebox-daemon.service', '[Unit]\n')
    system.enabled_user.add('jukebox-daemon.service')
    system.write('/etc/update-motd.d/99-rpi-jukebox-rfid-welcome', 'old')

    failed, _ = setup_run(system, home, answers={'samba': True})
    assert failed == 0
    assert 'Lauschkiste Boot Config' not in system.read('/boot/firmware/config.txt')
    smb = system.read('/etc/samba/smb.conf')
    assert smb.count('Samba Config') == 1 and '[jukebox]' not in smb and smb.startswith('[global]\n')
    assert f'path={home / "audiofolders"}\n' in smb
    assert not system.exists('~/.config/systemd/user/jukebox-daemon.service')
    assert 'jukebox-daemon.service' not in system.enabled_user
    assert 'lauschkiste.service' in system.enabled_user
    assert not system.exists('/etc/update-motd.d/99-rpi-jukebox-rfid-welcome')
    assert system.exists('/etc/update-motd.d/99-lauschkiste-welcome')


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
    assert extras == ['lauschkiste-plugin-rfid-readers[rc522-spi]']


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
    system.write('/etc/x.conf', '[global]\n  a=1\n\n## Jukebox Samba Config\n[jukebox]\n  path=/old\n\n[other]\n  b=2\n')
    system.replace_block('/etc/x.conf', '## Lauschkiste Samba Config', '[lauschkiste]\n  path=/new')
    assert system.read('/etc/x.conf') == ('[global]\n  a=1\n\n## Lauschkiste Samba Config\n[lauschkiste]\n'
                                          '  path=/new\n\n[other]\n  b=2\n')
    assert system.read_block('/etc/x.conf', '## Lauschkiste Samba Config') == (
        '## Lauschkiste Samba Config\n[lauschkiste]\n  path=/new')
