#!/usr/bin/env python3
"""Make a package index (PEP 503) from the files in a directory, to install from it like from PyPI.

    ci/make_index.py dist index      -> index/simple/<package>/...; serve ``index`` and use .../simple/
"""

import hashlib
import html
import re
import shutil
import sys
from pathlib import Path


def project_of(filename: str) -> str:
    stem = filename[:-4] if filename.endswith('.whl') else re.sub(r'\.(tar\.gz|zip)$', '', filename)
    name = stem.split('-')[0] if filename.endswith('.whl') else stem.rsplit('-', 1)[0]
    return re.sub(r'[-_.]+', '-', name).lower()


def main(source: Path, target: Path) -> None:
    files = sorted(path for path in source.iterdir() if path.suffix in ('.whl', '.zip') or path.name.endswith('.tar.gz'))
    if not files:
        sys.exit(f'no distributions in {source}')
    projects = {}
    for path in files:
        projects.setdefault(project_of(path.name), []).append(path)
    simple = target / 'simple'
    shutil.rmtree(simple, ignore_errors=True)
    for project, paths in projects.items():
        directory = simple / project
        directory.mkdir(parents=True)
        links = []
        for path in paths:
            shutil.copyfile(path, directory / path.name)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            links.append(f'<a href="{html.escape(path.name)}#sha256={digest}">{html.escape(path.name)}</a><br>')
        (directory / 'index.html').write_text('<!DOCTYPE html><html><body>\n' + '\n'.join(links) + '\n</body></html>\n')
    entries = '\n'.join(f'<a href="{project}/">{project}</a><br>' for project in sorted(projects))
    (simple / 'index.html').write_text(f'<!DOCTYPE html><html><body>\n{entries}\n</body></html>\n')
    print(f'{len(files)} files of {len(projects)} projects in {simple}')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
