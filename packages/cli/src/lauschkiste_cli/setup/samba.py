"""The Samba share of the library, used by `lauschctl setup samba` and the samba plugin."""

from typing import Optional

from lauschkiste_cli.setup.system import System

CONF = '/etc/samba/smb.conf'
MARKER = '## Lauschkiste Samba Config'
SHARE = 'lauschkiste'
MIN_PASSWORD = 8


def share_block(user: str, path: str) -> str:
    """Only the library: settings, card database and logs stay off the network."""
    return (
        f'[{SHARE}]\n'
        '  comment=Lauschkiste library\n'
        f'  path={path}\n'
        '  browseable=yes\n'
        '  writeable=yes\n'
        '  guest ok=no\n'
        f'  valid users={user}\n'
        f'  force user={user}\n'
        '  create mask=0664\n'
        '  directory mask=0775')


def installed(system: System) -> bool:
    return system.exists(CONF) and bool(system.which('smbpasswd') or system.exists('/usr/bin/smbpasswd'))


def has_user(system: System) -> bool:
    command = [*system.sudo, 'pdbedit', '-L'] if system.use_sudo else ['pdbedit', '-L']
    users = system.output(*command)
    return any(line.split(':')[0] == system.user for line in users.splitlines())


def current_block(system: System) -> Optional[str]:
    return system.read_block(CONF, MARKER)


def is_current(system: System, path: str) -> bool:
    block = current_block(system)
    return block is not None and block.split('\n')[1:] == share_block(system.user, path).split('\n')


def set_password(system: System, password: str) -> None:
    if len(password) < MIN_PASSWORD:
        raise ValueError(f'The password needs at least {MIN_PASSWORD} characters.')
    system.run('smbpasswd', '-s', '-a', system.user, root=True, input=f'{password}\n{password}\n', quiet=True)


def share(system: System, path: str) -> None:
    system.replace_block(CONF, MARKER, share_block(system.user, path), root=True)
    system.run('systemctl', 'restart', 'smbd', root=True, check=False, quiet=True)


def unshare(system: System) -> None:
    if system.remove_block(CONF, MARKER, root=True):
        system.run('systemctl', 'restart', 'smbd', root=True, check=False, quiet=True)
