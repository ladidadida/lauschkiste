"""`lauschctl uninstall`: remove what Lauschkiste put on this machine, and itself at the end.

Only what Lauschkiste created is removed: its services, files, marked blocks in system files, the shell profile lines
and the installation. What belongs to the system (packages, boot and network settings, users) stays and is listed
with the command to undo it by hand.
"""

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Tuple

import typer

import lauschkiste.common.paths
from lauschkiste_cli.environment import checkout
from lauschkiste_cli.setup import samba
from lauschkiste_cli.setup.steps import extras, lauschkiste as lauschkiste_steps, system as system_steps
from lauschkiste_cli.setup.system import System

PROFILE_MARKER = '# lauschkiste (added by install.sh)'
VENV_DIR = '~/.local/share/lauschkiste-venv'
COMMANDS = ('lauschctl', 'lauschkiste', 'bam')


@dataclass
class Action:
    text: str
    run: Callable[[], None]


def has_marker(system: System, path: str, marker: str) -> bool:
    return marker in (system.read(path) or '')


def _profile_lines(system: System, path: str) -> bool:
    """Remove every line the installer added (marker line and the line after it); False if there is none."""
    lines = (system.read(path) or '').split('\n')
    kept, changed, skip = [], False, False
    for line in lines:
        if skip:
            skip = False
            continue
        if line.strip() == PROFILE_MARKER:
            changed = skip = True
            if kept and not kept[-1].strip():
                kept.pop()
            continue
        kept.append(line)
    if changed:
        system.write(path, '\n'.join(kept))
    return changed


def _install_kind() -> Tuple[str, Optional[Path]]:
    """('source', checkout), ('venv', directory), ('uv', None) or ('other', None) for the running installation."""
    root = checkout()
    if root is not None:
        return 'source', root
    prefix = Path(sys.prefix).resolve()
    venv = Path(VENV_DIR).expanduser().resolve()
    if prefix == venv:
        return 'venv', venv
    if 'uv/tools' in str(prefix):
        return 'uv', None
    return 'other', None


def _our_links() -> List[Path]:
    """The commands in ~/.local/bin that point into this installation."""
    kind, root = _install_kind()
    bin_dir = Path.home() / '.local' / 'bin'
    links = []
    for name in COMMANDS:
        link = bin_dir / name
        if link.is_symlink():
            target = str(link.resolve(strict=False))
            if kind in ('venv', 'source') and root is not None and target.startswith(str(root)):
                links.append(link)
    return links


def _service_actions(system: System) -> List[Action]:
    actions: List[Action] = []
    unit = lauschkiste_steps.ServiceStep.UNIT_PATH
    if system.exists(unit):
        def stop_service() -> None:
            system.run('systemctl', '--user', 'disable', '--now', lauschkiste_steps.SERVICE, check=False)
            system.remove(unit)
            system.run('systemctl', '--user', 'daemon-reload', check=False)
        actions.append(Action(f'stop and remove the service {lauschkiste_steps.SERVICE}', stop_service))

    if system.exists(lauschkiste_steps.HTTP_SOCKET) or system.exists(lauschkiste_steps.HTTP_SERVICE):
        def forwarding() -> None:
            system.run('systemctl', 'disable', '--now', 'lauschkiste-http.socket', 'lauschkiste-http.service',
                       root=True, check=False)
            for path in (lauschkiste_steps.HTTP_SOCKET, lauschkiste_steps.HTTP_SERVICE):
                system.remove(path, root=True)
            system.run('systemctl', 'daemon-reload', root=True, check=False)
        actions.append(Action('remove the forwarding of port 80', forwarding))
    return actions


def _file_actions(system: System) -> List[Action]:
    actions: List[Action] = []
    for path, text in ((lauschkiste_steps.WebPortStep.OLD_SYSCTL, 'remove the old port setting'),
                       (system_steps.WelcomeStep.TARGET, 'remove the login message'),
                       (extras.KioskStep.LOADING, 'remove the loading page of the kiosk')):
        if system.exists(path):
            actions.append(Action(text, lambda p=path: system.remove(p, root=True)))
    kiosk = extras.KioskStep
    for path in ('/etc/chromium.d/01-disable-update-check',
                 '/etc/chromium-browser/customizations/01-disable-update-check'):
        if has_marker(system, path, kiosk.MARKER):
            actions.append(Action(f'remove {path}', lambda p=path: system.remove(p, root=True)))
    return actions


BOOT_MARKER = '## Lauschkiste Boot Config'


def _block_actions(system: System) -> List[Action]:
    """Blocks Lauschkiste added to files that belong to the system or the user."""
    kiosk = extras.KioskStep
    boot_config = str(system.boot_file('config.txt'))
    blocks = [(kiosk.BASHRC, kiosk.MARKER, False, f'remove the kiosk mode from {kiosk.BASHRC}'),
              (kiosk.AUTOSTART, kiosk.MARKER, True, f'remove the kiosk mode from {kiosk.AUTOSTART}'),
              (boot_config, BOOT_MARKER, True, 'remove the splash setting from config.txt')]
    actions = [Action(text, lambda p=path, m=marker, r=root: system.remove_marked(p, m, root=r))
               for path, marker, root, text in blocks if has_marker(system, path, marker)]
    if has_marker(system, samba.CONF, samba.MARKER):
        def share() -> None:
            system.remove_marked(samba.CONF, samba.MARKER, root=True)
            system.run('systemctl', 'restart', 'smbd', root=True, check=False)
        actions.append(Action('remove the Samba share of the library', share))
    for profile in ('~/.profile', '~/.bashrc'):
        if has_marker(system, profile, PROFILE_MARKER):
            actions.append(Action(f'remove the lines the installer added to {profile}',
                                  lambda p=profile: _profile_lines(system, p)))
    return actions


def plan(system: System, remove_data: bool) -> Tuple[List[Action], List[Action], List[str]]:
    """(actions, the removal of the installation itself, what stays), in the order they run."""
    actions = _service_actions(system) + _file_actions(system) + _block_actions(system)
    home = lauschkiste.common.paths.home()
    if remove_data and home.exists():
        actions.append(Action(f'DELETE the data in {home} (settings, cards, library, logs, cache)',
                              lambda: shutil.rmtree(home)))
    return actions, _removal_of_the_installation(), _stays(system, remove_data)


def _removal_of_the_installation() -> List[Action]:
    kind, root = _install_kind()
    links = _our_links()
    actions = [Action(f'remove the command {link}', link.unlink) for link in links]
    if kind == 'venv' and root is not None:
        actions.append(Action(f'remove the installation {root}', lambda: shutil.rmtree(root)))
    elif kind == 'uv':
        actions.append(Action('remove the installation with uv (uv tool uninstall lauschkiste)',
                              lambda: subprocess.run(['uv', 'tool', 'uninstall', 'lauschkiste'], check=False)))
    elif kind == 'source' and root is not None:
        actions.append(Action(f'(the checkout {root} stays: delete the folder yourself)', lambda: None))
    return actions


def _stays(system: System, remove_data: bool) -> List[str]:
    stays = []
    if not remove_data:
        stays.append(f'the data in {lauschkiste.common.paths.home()} (music, settings, cards): delete it by hand if wanted')
    stays += [
        'system packages installed for Lauschkiste (ffmpeg, pipewire, samba, openbox, chromium, ...): '
        'sudo apt remove <package> and sudo apt autoremove',
        'boot settings: the sound card, I2C/SPI and power-off lines in config.txt (a backup is config.txt.backup), '
        'quiet boot in cmdline.txt, switched-off Bluetooth (an older setup also switched off IPv6 and the apt timers)',
        'network settings: the WiFi hotspot, a static IP address (set by an older setup), the console autologin '
        'of the kiosk mode',
        'the Samba user and its password: sudo smbpasswd -x <user>',
        'lingering of the user service: sudo loginctl disable-linger <user>',
        'uv and its cache (if it was installed for Lauschkiste), and the piwheels entry in ~/.config/uv/uv.toml',
    ]
    return stays


def uninstall(check: bool = typer.Option(False, '--check', help='Only list what would be removed'),
              yes: bool = typer.Option(False, '--yes', '-y', help="Don't ask"),
              remove_data: bool = typer.Option(False, '--remove-data',
                                               help='Also delete the data (settings, cards, library)')) -> None:
    """Remove what Lauschkiste put on this machine, and Lauschkiste itself at the end."""
    system = System()
    if not check and not yes and not remove_data and lauschkiste.common.paths.home().exists():
        remove_data = typer.confirm(f"Delete the data in {lauschkiste.common.paths.home()} (settings, cards, library) too?",
                                    default=False)
    actions, itself, stays = plan(system, remove_data)
    everything = actions + itself
    typer.echo(typer.style('This removes:', bold=True) if everything else 'Nothing of Lauschkiste was found to remove.')
    for action in everything:
        typer.echo(f'  - {action.text}')
    typer.echo(typer.style('This stays:', bold=True))
    for text in stays:
        typer.echo(f'  - {text}')
    if check or not everything:
        return
    if not yes and not typer.confirm('Remove it now?', default=False):
        raise typer.Exit(1)
    for action in actions:
        typer.echo(f'==> {action.text}')
        action.run()
    typer.echo(typer.style('Lauschkiste is removed.', fg='green'))
    for action in itself:
        action.run()
