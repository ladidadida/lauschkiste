"""Access to the machine for setup steps: commands, files, facts. Tests replace it with a fake."""

import getpass
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, List, Optional, Union

import typer

PathLike = Union[str, Path]


def _block_span(lines: List[str], marker: str):
    """(start, end) of a marked block: the marker line, one ``[section]`` line, then indented lines."""
    for start, line in enumerate(lines):
        if line.strip() == marker:
            end = start + 1
            if end < len(lines) and lines[end].startswith('['):
                end += 1
            while end < len(lines) and lines[end][:1] in (' ', '\t'):
                end += 1
            return start, end
    return None


class SetupError(Exception):
    pass


class StepSkipped(Exception):
    """The step can't run now (e.g. needs interaction); not an error."""


class System:
    def __init__(self, root: PathLike = '/'):
        #: Prefix for all absolute paths (a directory tree standing in for / in tests)
        self.root = Path(root)
        #: Whether commands/writes marked as root need ``sudo``
        self.use_sudo = os.geteuid() != 0

    # --- files -----------------------------------------------------------------------------------

    def path(self, path: PathLike) -> Path:
        path = Path(path).expanduser()
        if self.root == Path('/') or not path.is_absolute():
            return path
        return self.root / path.relative_to('/')

    def exists(self, path: PathLike) -> bool:
        return self.path(path).exists()

    def read(self, path: PathLike) -> Optional[str]:
        try:
            return self.path(path).read_text()
        except (FileNotFoundError, PermissionError, IsADirectoryError):
            return None

    def write(self, path: PathLike, text: str, root: bool = False, mode: int = 0o644) -> None:
        target = self.path(path)
        if root and self.use_sudo:
            self.run('mkdir', '-p', str(target.parent), root=True)
            self.run('tee', str(target), root=True, input=text, quiet=True)
            self.run('chmod', f'{mode:o}', str(target), root=True)
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        target.chmod(mode)

    def append_block(self, path: PathLike, marker: str, block: str, root: bool = False) -> bool:
        """Append ``marker`` + ``block`` unless the file already contains ``marker``."""
        current = self.read(path) or ''
        if marker in current:
            return False
        separator = '' if not current or current.endswith('\n') else '\n'
        self.write(path, f"{current}{separator}\n{marker}\n{block.rstrip()}\n", root=root)
        return True

    def read_block(self, path: PathLike, marker: str) -> Optional[str]:
        """The block ``append_block`` added (marker line through the indented lines of its first
        section); None if there is none."""
        lines = (self.read(path) or '').split('\n')
        span = _block_span(lines, marker)
        return None if span is None else '\n'.join(lines[span[0]:span[1]])

    def replace_block(self, path: PathLike, marker: str, block: str, root: bool = False) -> None:
        """Replace the block marked ``marker`` in place, else append it."""
        lines = (self.read(path) or '').split('\n')
        span = _block_span(lines, marker)
        if span is None:
            self.append_block(path, marker, block, root=root)
            return
        lines[span[0]:span[1]] = [marker, *block.rstrip().split('\n')]
        self.write(path, '\n'.join(lines), root=root)

    def remove(self, path: PathLike, root: bool = False) -> None:
        target = self.path(path)
        if not target.exists():
            return
        if root and self.use_sudo:
            self.run('rm', '-f', str(target), root=True)
        else:
            target.unlink()

    # --- commands --------------------------------------------------------------------------------

    def which(self, command: str) -> Optional[str]:
        return shutil.which(command)

    def run(self, *args: str, root: bool = False, check: bool = True, input: Optional[str] = None,
            quiet: bool = False) -> subprocess.CompletedProcess:
        command = ['sudo', *args] if root and self.use_sudo else list(args)
        if not quiet:
            typer.echo(f"  $ {' '.join(command)}")
        result = subprocess.run(command, input=input, text=True,
                                stdout=subprocess.DEVNULL if quiet else None)
        if check and result.returncode != 0:
            raise SetupError(f"'{' '.join(command)}' failed with exit code {result.returncode}")
        return result

    def output(self, *args: str) -> str:
        """Stdout of a query command, '' if it fails or doesn't exist."""
        try:
            result = subprocess.run(list(args), capture_output=True, text=True)
        except (FileNotFoundError, PermissionError):
            return ''
        return result.stdout.strip() if result.returncode == 0 else ''

    # --- facts -----------------------------------------------------------------------------------

    @property
    def user(self) -> str:
        return getpass.getuser()

    def architecture(self) -> str:
        machine = platform.machine()
        return {'armv7l': 'armv7', 'armv6l': 'armv6', 'aarch64': 'arm64'}.get(machine, machine)

    def is_raspberry_pi(self) -> bool:
        model = self.read('/proc/device-tree/model') or ''
        return 'Raspberry Pi' in model

    def is_debian(self) -> bool:
        return self.exists('/usr/bin/apt-get') or self.which('apt-get') is not None

    def unit_active(self, unit: str, user: bool = False) -> bool:
        args = ['systemctl', *(['--user'] if user else []), 'is-active', unit]
        return self.output(*args) == 'active'

    def unit_enabled(self, unit: str, user: bool = False) -> bool:
        args = ['systemctl', *(['--user'] if user else []), 'is-enabled', unit]
        return self.output(*args) == 'enabled'

    def missing_packages(self, packages: Iterable[str]) -> List[str]:
        missing = []
        for package in packages:
            status = self.output('dpkg-query', '-W', '-f', '${Status}', package)
            if not status or status.split()[-1] != 'installed':
                missing.append(package)
        return missing

    def boot_file(self, name: str) -> Path:
        return Path('/boot/firmware') / name
