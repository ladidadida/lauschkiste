"""`jukebox update`: newer release (package install) or `git pull` (source checkout)."""

import re
import shutil
import subprocess
import tempfile
from importlib.metadata import PackageNotFoundError, version as installed_version
from pathlib import Path
from typing import Dict, List, Optional

import typer
from packaging.version import Version

import jukebox.paths
from jukebox_cli import plugin
from jukebox_cli.environment import DEFAULT_REPO, checkout, jukebox_executable
from jukebox_cli.setup.base import Context
from jukebox_cli.setup.system import System

SERVICE = 'jukebox-daemon.service'


class UpdateError(Exception):
    pass


def run(*args: str, cwd: Optional[Path] = None, capture: bool = False) -> str:
    if not capture:
        typer.echo(f"  $ {' '.join(args)}")
    result = subprocess.run(list(args), cwd=cwd, text=True, capture_output=capture)
    if result.returncode != 0:
        raise UpdateError(f"'{' '.join(args)}' failed{': ' + result.stderr.strip() if capture else ''}")
    return (result.stdout or '').strip()


# --- source checkout ---------------------------------------------------------------------------

def update_source(root: Path, check_only: bool = False) -> bool:
    """Pull, sync the environment, rebuild the web app if it changed. True if something changed."""
    try:
        upstream = run('git', 'rev-parse', '--abbrev-ref', '@{u}', cwd=root, capture=True)
    except UpdateError:
        raise UpdateError(f"the current branch of {root} has no upstream branch; update it with git") from None
    run('git', 'fetch', '--quiet', cwd=root)
    behind = int(run('git', 'rev-list', '--count', 'HEAD..@{u}', cwd=root, capture=True) or 0)
    if not behind:
        typer.echo(f"{root} is up to date.")
        return False
    typer.echo(f"{root} is {behind} commit(s) behind {upstream}.")
    if check_only:
        return True
    before = run('git', 'rev-parse', 'HEAD', cwd=root, capture=True)
    run('git', 'pull', '--ff-only', cwd=root)
    uv = shutil.which('uv')
    if uv is None:
        raise UpdateError("uv is not on PATH; run 'uv sync --no-dev --frozen' in the checkout yourself")
    run(uv, 'sync', '--no-dev', '--frozen', cwd=root)
    webapp_changed = run('git', 'diff', '--name-only', before, 'HEAD', '--', 'packages/webapp', cwd=root,
                         capture=True)
    if webapp_changed:
        npm = shutil.which('npm')
        if npm:
            run(npm, 'ci', cwd=root / 'packages' / 'webapp')
            run(npm, 'run', 'build', cwd=root / 'packages' / 'webapp')
        else:
            typer.echo("The web app changed, but npm is not installed: rebuild it elsewhere "
                       "or download a release build (see install.sh).")
    return True


# --- package install ---------------------------------------------------------------------------

def fetch_release(repo: str, tag: str = 'latest') -> dict:
    url = f'https://api.github.com/repos/{repo}/releases/' + ('latest' if tag == 'latest' else f'tags/{tag}')
    import requests
    response = requests.get(url, timeout=30)
    if response.status_code == 404:
        raise UpdateError(f"no release '{tag}' in {repo}")
    response.raise_for_status()
    return response.json()


def release_version(release: dict) -> Version:
    return Version(release['tag_name'].lstrip('v'))


def _dist_name(wheel: str) -> str:
    return re.sub(r'[-_.]+', '-', wheel.split('-', 1)[0]).lower()


def wheel_requirements(wheels: List[Path], extras: Dict[str, List[str]]) -> List[str]:
    """``name[extras] @ file://...`` for each wheel, keeping the extras enabled plugins need."""
    requirements = []
    for wheel in wheels:
        name = _dist_name(wheel.name)
        suffix = f"[{','.join(sorted(extras[name]))}]" if extras.get(name) else ''
        requirements.append(f"{name}{suffix} @ {wheel.resolve().as_uri()}")
    return requirements


def enabled_extras(config_path: Path) -> Dict[str, List[str]]:
    """Distribution -> extras, for the plugins enabled in the configuration."""
    extras: Dict[str, List[str]] = {}
    if not config_path.exists():
        return extras
    for name in Context(System(), config_path).enabled_plugins():
        for requirement in plugin.plugin_extras(name):
            dist, _, rest = requirement.partition('[')
            extras.setdefault(_dist_name(dist), []).extend(rest.rstrip(']').split(','))
    return extras


def update_package(repo: str, tag: str, config_path: Path, check_only: bool = False) -> bool:
    try:
        current = Version(installed_version('jukebox'))
    except PackageNotFoundError:
        current = Version('0')
    release = fetch_release(repo, tag)
    target = release_version(release)
    if tag == 'latest' and target <= current:
        typer.echo(f"jukebox {current} is up to date (latest release: {target}).")
        return False
    typer.echo(f"Updating jukebox {current} -> {target}")
    if check_only:
        return True
    assets = [asset for asset in release.get('assets', []) if asset['name'].endswith('.whl')]
    if not assets:
        raise UpdateError(f"release {release['tag_name']} has no wheels")
    with tempfile.TemporaryDirectory() as tmp:
        wheels = []
        for asset in assets:
            path = Path(tmp) / asset['name']
            import requests
            response = requests.get(asset['browser_download_url'], timeout=120)
            response.raise_for_status()
            path.write_bytes(response.content)
            wheels.append(path)
        plugin.install_requirements(wheel_requirements(wheels, enabled_extras(config_path)))
    return True


# --- command -----------------------------------------------------------------------------------

def restart_service() -> None:
    if subprocess.run(['systemctl', '--user', 'is-active', '--quiet', SERVICE], check=False).returncode == 0:
        run('systemctl', '--user', 'restart', SERVICE)


def update(release: str = typer.Option('latest', "--version", help="Release tag to install (package installs)"),
           repo: str = typer.Option(DEFAULT_REPO, "--repo", envvar="JUKEBOX_REPO", help="GitHub repository"),
           check: bool = typer.Option(False, "--check", help="Only report whether an update is available"),
           setup: bool = typer.Option(True, "--setup/--no-setup",
                                      help="Re-apply `jukebox setup` with the stored answers afterwards"),
           conf: Optional[Path] = typer.Option(None, "-c", "--conf", envvar="JUKEBOX_CONF",
                                               help="Jukebox configuration file")) -> None:
    """Update the jukebox: newer release, or `git pull` + `uv sync` in a source checkout."""
    config_path = conf or jukebox.paths.settings_dir() / 'jukebox.yaml'
    root = checkout()
    try:
        changed = update_source(root, check) if root else update_package(repo, release, config_path, check)
    except (UpdateError, OSError) as error:
        typer.echo(f"Update failed: {error}", err=True)
        raise typer.Exit(1)
    if check or not changed:
        return
    if setup:
        # In a new process: the updated setup steps, not the ones already imported here
        result = subprocess.run([jukebox_executable(), 'setup', '--yes', *(['--conf', str(conf)] if conf else [])],
                                check=False)
        if result.returncode != 0:
            typer.echo("Some setup steps are not complete, see above ('jukebox setup --check').", err=True)
    restart_service()
    typer.echo("Update complete.")

