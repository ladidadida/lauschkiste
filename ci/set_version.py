#!/usr/bin/env python3
"""Set the version of all packages at once: ``ci/set_version.py 0.1.0-alpha.4`` (or ``0.1.0a4``).

Changes the version of every package, the exact pins between them and ``lauschkiste/version.py``.
A test upload to TestPyPI needs a new version each time: ``0.1.0a4.dev1``, ``0.1.0a4.dev2``, ...
"""

import re
import sys
from pathlib import Path

from packaging.version import Version

ROOT = Path(__file__).resolve().parent.parent
PYPROJECTS = sorted(ROOT.glob('packages/*/pyproject.toml')) + sorted(ROOT.glob('packages/plugins/*/pyproject.toml'))
VERSION_FILE = ROOT / 'packages/lauschkiste/src/lauschkiste/version.py'
PINNED = ('lauschkiste-core', 'lauschkiste')


def runtime_parts(version: Version):
    """(major, minor, patch, extra) for version.py: 0.1.0a4.dev1 -> (0, 1, 0, 'alpha.4.dev1')."""
    names = {'a': 'alpha', 'b': 'beta', 'rc': 'rc'}
    parts = []
    if version.pre:
        parts.append(f'{names[version.pre[0]]}.{version.pre[1]}')
    if version.post is not None:
        parts.append(f'post{version.post}')
    if version.dev is not None:
        parts.append(f'dev{version.dev}')
    return version.major, version.minor, version.micro, '.'.join(parts)


def main(argv):
    if len(argv) != 2:
        sys.exit(__doc__)
    version = Version(argv[1])
    for path in PYPROJECTS:
        text = path.read_text()
        text = re.sub(r'^version = ".*"$', f'version = "{version}"', text, count=1, flags=re.M)
        for name in PINNED:
            text = re.sub(rf'^(\s+"{re.escape(name)}==)[^"]+(")', rf'\g<1>{version}\g<2>', text, flags=re.M)
        path.write_text(text)
    major, minor, patch, extra = runtime_parts(version)
    text = VERSION_FILE.read_text()
    for key, value in (('MAJOR', major), ('MINOR', minor), ('PATCH', patch)):
        text = re.sub(rf'^VERSION_{key} = .*$', f'VERSION_{key} = {value}', text, flags=re.M)
    text = re.sub(r'^VERSION_EXTRA = .*$', f'VERSION_EXTRA = "{extra}"', text, flags=re.M)
    VERSION_FILE.write_text(text)
    print(f'version {version} in {len(PYPROJECTS)} packages and {VERSION_FILE.relative_to(ROOT)}')


if __name__ == '__main__':
    main(sys.argv)
