"""Check or update the stored interface snapshots of the framework, core modules and bundled plugins.

    uv run python -m lauschkiste.contract.snapshots            # check (what CI runs via pytest)
    uv run python -m lauschkiste.contract.snapshots --update   # write snapshots after a version bump
"""

import argparse
import inspect
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from lauschkiste.contract import interfaces
from lauschkiste.contract.manager import discover_plugins

_JUKEBOX_PACKAGE_ROOT = Path(__file__).resolve().parents[3]
CORE_SNAPSHOT_DIR = _JUKEBOX_PACKAGE_ROOT / 'interfaces'


@dataclass
class Target:
    label: str
    path: Path
    describe: Callable[[], Dict]
    compare: Callable[[Dict, Dict], Tuple[str, List[str]]]
    version_key: str


def _package_root(cls) -> Path:
    path = Path(inspect.getfile(cls)).resolve().parent
    for candidate in [path, *path.parents]:
        if (candidate / 'pyproject.toml').exists():
            return candidate
    raise RuntimeError(f"No pyproject.toml above {path}")


def targets(include_plugins: bool = True) -> List[Target]:
    from lauschkiste.core_modules import CORE_MODULES

    result = [Target('framework contract', CORE_SNAPSHOT_DIR / '_contract.json',
                     interfaces.describe_contract, interfaces.compare_contracts, 'contract_version')]
    for cls in sorted(CORE_MODULES, key=lambda c: c.name):
        result.append(Target(f"core module '{cls.name}'", CORE_SNAPSHOT_DIR / f'{cls.name}.json',
                             lambda cls=cls: interfaces.describe_module_interface(cls),
                             interfaces.compare_module_interfaces, 'interface_version'))
    if include_plugins:
        for name, load in sorted(discover_plugins().items()):
            cls = load()
            root = _package_root(cls)
            if root.parent.name != 'plugins':
                continue  # only bundled plugins (packages/plugins/<name>) are tracked here
            result.append(Target(f"plugin '{name}'", root / 'interfaces' / f'{name}.json',
                                 lambda cls=cls: interfaces.describe_module_interface(cls),
                                 interfaces.compare_module_interfaces, 'interface_version'))
    return result


def check_target(target: Target) -> Optional[str]:
    """Return a problem description, or None when the stored snapshot matches."""
    current = target.describe()
    if not target.path.exists():
        return f"{target.label}: no snapshot at {target.path}"
    stored = interfaces.load_snapshot(target.path)
    level, notes = target.compare(stored, current)
    old_version, new_version = stored[target.version_key], current[target.version_key]
    if not interfaces.required_bump_satisfied(level, old_version, new_version):
        details = '\n    '.join(notes)
        return (f"{target.label}: {level} change needs a version bump "
                f"(snapshot {old_version}, code {new_version}):\n    {details}")
    if stored != current:
        return f"{target.label}: snapshot out of date (version bump is fine, run with --update)"
    return None


def update_target(target: Target) -> Optional[str]:
    current = target.describe()
    if target.path.exists():
        stored = interfaces.load_snapshot(target.path)
        level, notes = target.compare(stored, current)
        if not interfaces.required_bump_satisfied(level, stored[target.version_key], current[target.version_key]):
            details = '\n    '.join(notes)
            return (f"{target.label}: refusing to update, {level} change needs a version bump "
                    f"(currently {current[target.version_key]}):\n    {details}")
    interfaces.write_snapshot(target.path, current)
    return None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--update', action='store_true', help='write snapshots (refuses missing version bumps)')
    args = parser.parse_args(argv)
    problems = [p for p in ((update_target if args.update else check_target)(t) for t in targets()) if p]
    for problem in problems:
        print(problem, file=sys.stderr)
    if not problems:
        print('Interface snapshots ' + ('updated.' if args.update else 'match.'))
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
