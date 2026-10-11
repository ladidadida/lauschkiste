import pytest
from typer.testing import CliRunner

import lauschkiste.common.paths
from lauschkiste_cli import uninstall as uninstall_module
from lauschkiste_cli.setup.system import System
from lauschkiste_cli.uninstall import PROFILE_MARKER, _profile_lines, plan


class RecordingSystem(System):
    def __init__(self, root):
        super().__init__(root)
        self.use_sudo = False
        self.commands = []

    def run(self, *args, root=False, check=True, input=None, quiet=False):
        self.commands.append(args)


@pytest.fixture
def system(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path / 'root' / 'home' / 'pi'))
    lauschkiste.common.paths.set_home(tmp_path / 'root' / 'home' / 'pi' / 'lauschkiste')
    monkeypatch.setattr(uninstall_module, '_install_kind', lambda: ('other', None))
    yield RecordingSystem(tmp_path / 'root')
    lauschkiste.common.paths.set_home(None)


def test_a_marked_block_is_removed_with_its_blank_line_and_nothing_else(system):
    system.write('/etc/x.conf', 'keep1\n\n## Lauschkiste Boot Config\ndisable_splash=1\n\nkeep2\n')
    assert system.remove_marked('/etc/x.conf', '## Lauschkiste Boot Config')
    assert system.read('/etc/x.conf') == 'keep1\n\nkeep2\n'
    assert not system.remove_marked('/etc/x.conf', '## Lauschkiste Boot Config')


def test_profile_lines_of_the_installer_are_removed(system):
    system.write('~/.profile', f'before\n\n{PROFILE_MARKER}\nexport PATH="$HOME/.local/bin:$PATH"\n\n{PROFILE_MARKER}\n'
                               'export LAUSCHKISTE_HOME="/x"\nafter\n')
    assert _profile_lines(system, '~/.profile')
    assert system.read('~/.profile') == 'before\nafter\n'


def test_nothing_found_means_nothing_to_remove(system):
    actions, itself, stays = plan(system, remove_data=False)
    assert actions == [] and itself == [] and stays


def test_services_files_blocks_and_data_are_removed(system):
    system.write('~/.config/systemd/user/lauschkiste.service', '[Unit]\n')
    system.write('/etc/systemd/system/lauschkiste-http.socket', '[Socket]\n')
    system.write('/etc/update-motd.d/99-lauschkiste-welcome', '#!/bin/sh\n')
    system.write('/etc/samba/smb.conf', '[global]\n  a=b\n\n## Lauschkiste Samba Config\n[lauschkiste]\n  path=/x\n')
    (lauschkiste.common.paths.home() / 'settings').mkdir(parents=True)
    actions, _, stays = plan(system, remove_data=True)
    texts = [action.text for action in actions]
    assert any('service lauschkiste.service' in text for text in texts)
    assert any('forwarding of port 80' in text for text in texts)
    assert any('Samba share' in text for text in texts)
    assert any(text.startswith('DELETE the data') for text in texts)
    for action in actions:
        action.run()
    assert not system.exists('~/.config/systemd/user/lauschkiste.service')
    assert not system.exists('/etc/systemd/system/lauschkiste-http.socket')
    assert not system.exists('/etc/update-motd.d/99-lauschkiste-welcome')
    assert system.read('/etc/samba/smb.conf') == '[global]\n  a=b\n'
    assert not lauschkiste.common.paths.home().exists()
    assert ('systemctl', '--user', 'disable', '--now', 'lauschkiste.service') in system.commands
    assert not any('the data in' in text for text in stays)


def test_the_data_stays_unless_asked(system):
    (lauschkiste.common.paths.home() / 'settings').mkdir(parents=True)
    actions, _, stays = plan(system, remove_data=False)
    assert not any('DELETE' in action.text for action in actions)
    assert any('the data in' in text for text in stays)


def test_check_lists_everything_and_changes_nothing(system, monkeypatch):
    system.write('/etc/update-motd.d/99-lauschkiste-welcome', '#!/bin/sh\n')
    monkeypatch.setattr(uninstall_module, 'System', lambda: system)
    from lauschkiste_cli.cli import ctl
    result = CliRunner().invoke(ctl, ['uninstall', '--check'])
    assert result.exit_code == 0
    assert 'remove the login message' in result.output and 'This stays' in result.output
    assert system.exists('/etc/update-motd.d/99-lauschkiste-welcome')
