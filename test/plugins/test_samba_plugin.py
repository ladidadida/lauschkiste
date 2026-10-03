from pathlib import Path
from unittest.mock import Mock

import pytest

import lauschkiste.library
import lauschkiste_plugin_samba
from lauschkiste.contract import OperationError
from lauschkiste_cli.setup import samba
from lauschkiste_cli.setup.system import System

CONF = 'workgroup = WORKGROUP\n\n[homes]\n  browseable = no\n'


class FakeSystem(System):
    def __init__(self, root, users=''):
        super().__init__(root)
        self.use_sudo = False
        self.commands = []
        self.users = users

    def which(self, command):
        return f'/usr/bin/{command}'

    def output(self, *args):
        return self.users if 'pdbedit' in args else ''

    def run(self, *args, root=False, check=True, input=None, quiet=False):
        self.commands.append((args, input))
        if args[0] == 'smbpasswd':
            self.users = f'{self.user}:1000:'
        return Mock(returncode=0)


@pytest.fixture
def plugin(tmp_path, monkeypatch):
    (tmp_path / 'etc' / 'samba').mkdir(parents=True)
    (tmp_path / 'etc' / 'samba' / 'smb.conf').write_text(CONF)
    monkeypatch.setattr(lauschkiste.library, 'root', lambda: '/home/pi/lauschkiste/library')
    instance = lauschkiste_plugin_samba.Samba()
    instance._system = FakeSystem(tmp_path)
    return instance, tmp_path / 'etc' / 'samba' / 'smb.conf'


def test_share_password_and_unshare(plugin):
    instance, conf = plugin
    status = instance.get_status()
    assert (status.installed, status.shared, status.has_password) == (True, False, False)

    status = instance.set_share(True)
    assert status.shared and not status.outdated
    assert 'path=/home/pi/lauschkiste/library' in conf.read_text() and '[homes]' in conf.read_text()

    instance._run(lambda: samba.set_password(instance._system, 'geheim123'))
    assert instance.get_status().has_password
    assert (('smbpasswd', '-s', '-a', instance._system.user), 'geheim123\ngeheim123\n') in instance._system.commands

    status = instance.set_share(False)
    assert not status.shared
    assert conf.read_text() == CONF


def test_short_password_is_rejected(plugin):
    instance, _ = plugin
    with pytest.raises(ValueError):
        samba.set_password(instance._system, 'kurz')


def test_not_installed(plugin):
    instance, conf = plugin
    conf.unlink()
    assert not instance.get_status().installed
    with pytest.raises(OperationError) as error:
        instance.set_share(True)
    assert error.value.status == 409
    assert not Path(conf).exists()
