import tomllib
from pathlib import Path

from packaging.requirements import Requirement
from packaging.version import Version

import lauschkiste

ROOT = Path(__file__).resolve().parent.parent
PACKAGES = sorted(path.parent for path in [*ROOT.glob('packages/*/pyproject.toml'),
                                           *ROOT.glob('packages/plugins/*/pyproject.toml')])
PINNED = {'lauschkiste', 'lauschkiste-core'}


def project(directory: Path) -> dict:
    return tomllib.loads((directory / 'pyproject.toml').read_text())['project']


def test_distribution_names():
    names = {project(directory)['name'] for directory in PACKAGES}
    assert names == {'lauschkiste', 'lauschkiste-core', 'lauschkiste-plugin-board-raspberry-pi',
                     'lauschkiste-plugin-devices', 'lauschkiste-plugin-mpd', 'lauschkiste-plugin-rfid-readers',
                     'lauschkiste-plugin-samba', 'lauschkiste-plugin-audiobookshelf',
                     'lauschkiste-plugin-podcast-directories'}


def test_all_packages_have_the_version_of_the_program():
    expected = Version(lauschkiste.version())
    assert {project(directory)['version'] for directory in PACKAGES} == {str(expected)}


def test_packages_depend_on_exactly_the_same_version_of_each_other():
    version = project(ROOT / 'packages/cli')['version']
    pins = []
    for directory in PACKAGES:
        for requirement in map(Requirement, project(directory).get('dependencies', [])):
            if requirement.name in PINNED:
                pins.append((project(directory)['name'], requirement.name, str(requirement.specifier)))
    assert pins and all(specifier == f'=={version}' for _, _, specifier in pins), pins


def test_every_package_has_what_pypi_shows():
    license_text = (ROOT / 'LICENSE').read_text()
    for directory in PACKAGES:
        data = project(directory)
        name = data['name']
        assert (directory / 'README.md').read_text().startswith('# '), name
        assert (directory / 'LICENSE').read_text() == license_text, name
        assert data['readme'] == 'README.md' and data['license-files'] == ['LICENSE'], name
        assert data['authors'] and data['keywords'] and data['classifiers'], name
        assert {'Homepage', 'Issues', 'Documentation'} <= set(data['urls']), name
