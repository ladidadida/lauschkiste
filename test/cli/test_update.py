import subprocess

import pytest

import lauschkiste.paths
from lauschkiste_cli import plugin, update


def git(cwd, *args):
    subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@t', *args], cwd=cwd, check=True,
                   capture_output=True)


@pytest.fixture
def repos(tmp_path):
    origin, clone = tmp_path / 'origin', tmp_path / 'clone'
    origin.mkdir()
    git(origin, 'init', '-q', '-b', 'main')
    (origin / 'README').write_text('1')
    git(origin, 'add', '.')
    git(origin, 'commit', '-qm', 'one')
    git(tmp_path, 'clone', '-q', str(origin), str(clone))
    return origin, clone


@pytest.fixture
def commands(monkeypatch):
    recorded = []
    real_run = update.run

    def fake_run(*args, cwd=None, capture=False):
        if args[0] == 'git':
            return real_run(*args, cwd=cwd, capture=capture)
        recorded.append(args)
        return ''

    monkeypatch.setattr(update, 'run', fake_run)
    monkeypatch.setattr(update.shutil, 'which', lambda name: f'/usr/bin/{name}')
    return recorded


def test_source_up_to_date(repos, commands):
    assert update.update_source(repos[1]) is False
    assert commands == []


def test_source_update_pulls_syncs_and_builds_changed_webapp(repos, commands):
    origin, clone = repos
    (origin / 'packages' / 'webapp').mkdir(parents=True)
    (origin / 'packages' / 'webapp' / 'x.js').write_text('x')
    git(origin, 'add', '.')
    git(origin, 'commit', '-qm', 'two')
    assert update.update_source(clone, check_only=True) is True
    assert not (clone / 'packages').exists()
    assert update.update_source(clone) is True
    assert (clone / 'packages' / 'webapp' / 'x.js').exists()
    assert [c[1:] for c in commands] == [('sync', '--no-dev', '--frozen'), ('ci',), ('run', 'build')]


def test_source_without_upstream(tmp_path):
    git(tmp_path, 'init', '-q')
    with pytest.raises(update.UpdateError, match='no upstream'):
        update.update_source(tmp_path)


def test_wheel_requirements_keep_extras(tmp_path):
    wheels = [tmp_path / 'lauschkiste-3.8.0-py3-none-any.whl',
              tmp_path / 'lauschkiste_plugin_raspberry_pi-1.1.0-py3-none-any.whl']
    requirements = update.wheel_requirements(wheels, {'lauschkiste-plugin-raspberry-pi': ['gpio']})
    assert requirements == [f'lauschkiste @ {wheels[0].as_uri()}',
                            f'lauschkiste-plugin-raspberry-pi[gpio] @ {wheels[1].as_uri()}']


class FakeResponse:
    status_code = 200

    def __init__(self, payload=None, content=b''):
        self.payload, self.content = payload, content

    def json(self):
        return self.payload

    def raise_for_status(self):
        pass


def test_package_update(tmp_path, monkeypatch):
    release = {'tag_name': 'v99.0.0', 'assets': [
        {'name': 'lauschkiste-99.0.0-py3-none-any.whl', 'browser_download_url': 'https://x/lauschkiste.whl'},
        {'name': 'notes.txt', 'browser_download_url': 'https://x/notes.txt'}]}
    monkeypatch.setattr('requests.get',
                        lambda url, timeout: FakeResponse(release) if 'api.github' in url else FakeResponse(content=b'w'))
    installed = []
    monkeypatch.setattr(plugin, 'install_requirements', installed.extend)
    lauschkiste.paths.set_home(tmp_path)
    try:
        assert update.update_package('o/r', 'latest', tmp_path / 'lauschkiste.yaml') is True
    finally:
        lauschkiste.paths.set_home(None)
    assert len(installed) == 1 and installed[0].startswith('lauschkiste @ file://')


def test_package_up_to_date(monkeypatch):
    monkeypatch.setattr('requests.get', lambda url, timeout: FakeResponse({'tag_name': 'v0.0.1'}))
    assert update.update_package('o/r', 'latest', lauschkiste.paths.settings_dir() / 'x.yaml') is False


def test_latest_falls_back_to_the_newest_pre_release(monkeypatch):
    calls = []

    class NotFound(FakeResponse):
        status_code = 404

    def get(url, timeout, params=None):
        calls.append(url)
        if url.endswith('/latest'):
            return NotFound()
        return FakeResponse([{'tag_name': 'webapp-development', 'assets': [{'name': 'webapp.tar.gz'}]},
                             {'tag_name': 'v0.1.0-alpha.1', 'assets': [{'name': 'lauschkiste-0.1.0a1-py3-none-any.whl'}]}])

    monkeypatch.setattr('requests.get', get)
    assert update.fetch_release('o/r')['tag_name'] == 'v0.1.0-alpha.1'
    assert calls == ['https://api.github.com/repos/o/r/releases/latest', 'https://api.github.com/repos/o/r/releases']
    assert update.release_version({'tag_name': 'v0.1.0-alpha.1'}) > update.Version('0.1.0a0')


class FakeDist:
    def __init__(self, name):
        self.metadata = {'Name': name}


def pypi(releases):
    return FakeResponse({'releases': {version: [{'yanked': yanked}] if yanked is not None else []
                                      for version, yanked in releases.items()}})


def test_wheel_files_tell_a_package_from_an_index_install(monkeypatch):
    class Dist:
        def __init__(self, text):
            self.text = text

        def read_text(self, name):
            return self.text

    monkeypatch.setattr(update, 'distribution', lambda name: Dist('{"url": "file:///x.whl"}'))
    assert update.installed_from_wheel_files() is True
    monkeypatch.setattr(update, 'distribution', lambda name: Dist(None))
    assert update.installed_from_wheel_files() is False


def test_latest_index_version_is_the_newest_stable_else_the_newest_pre_release(monkeypatch):
    monkeypatch.setattr('requests.get', lambda url, timeout: pypi({'0.1.0a3': False, '0.1.0a4': False, '0.0.9': False}))
    assert str(update.latest_index_version()) == '0.0.9'
    monkeypatch.setattr('requests.get', lambda url, timeout: pypi({'0.1.0a3': False, '0.1.0a4': False}))
    assert str(update.latest_index_version()) == '0.1.0a4'
    monkeypatch.setattr('requests.get', lambda url, timeout: pypi({'0.1.0': False, '0.2.0a1': False, '0.1.1': True}))
    assert str(update.latest_index_version()) == '0.1.0'
    monkeypatch.setattr('requests.get', lambda url, timeout: pypi({'0.1.0a5': None}))
    with pytest.raises(update.UpdateError):
        update.latest_index_version()


def test_index_update_pins_all_installed_packages_and_keeps_extras(tmp_path, monkeypatch):
    monkeypatch.setattr('requests.get', lambda url, timeout: pypi({'0.1.0a3': False, '99.0.0': False}))
    monkeypatch.setattr(update, 'installed_version', lambda name: '0.1.0a3')
    monkeypatch.setattr(update, 'distributions', lambda: [FakeDist('lauschkiste'), FakeDist('lauschkiste_core'),
                                                          FakeDist('lauschkiste-plugin-devices'), FakeDist('typer')])
    monkeypatch.setattr(update, 'enabled_extras', lambda path: {'lauschkiste-plugin-devices': ['gpio']})
    installed = []
    monkeypatch.setattr(plugin, 'install_requirements', installed.extend)
    assert update.update_from_index('latest', tmp_path / 'x.yaml', check_only=True) is True
    assert installed == []
    assert update.update_from_index('latest', tmp_path / 'x.yaml') is True
    assert installed == ['lauschkiste==99.0.0', 'lauschkiste-core==99.0.0', 'lauschkiste-plugin-devices[gpio]==99.0.0']
    installed.clear()
    update.update_from_index('v0.1.0-alpha.4', tmp_path / 'x.yaml')
    assert installed[0] == 'lauschkiste==0.1.0a4'


def test_index_update_when_up_to_date(tmp_path, monkeypatch):
    monkeypatch.setattr('requests.get', lambda url, timeout: pypi({'0.1.0a3': False}))
    monkeypatch.setattr(update, 'installed_version', lambda name: '0.1.0a3')
    assert update.update_from_index('latest', tmp_path / 'x.yaml') is False


def test_update_command_picks_the_source_of_the_installation(tmp_path, monkeypatch):
    called = []
    monkeypatch.setattr(update, 'checkout', lambda: None)
    monkeypatch.setattr(update, 'update_package', lambda *args: called.append('github') or False)
    monkeypatch.setattr(update, 'update_from_index', lambda *args: called.append('index') or False)
    monkeypatch.setattr(update, 'installed_from_wheel_files', lambda: True)
    update.update('latest', 'o/r', True, False, tmp_path / 'x.yaml')
    monkeypatch.setattr(update, 'installed_from_wheel_files', lambda: False)
    update.update('latest', 'o/r', True, False, tmp_path / 'x.yaml')
    monkeypatch.setattr(update, 'checkout', lambda: tmp_path)
    monkeypatch.setattr(update, 'update_source', lambda *args: called.append('source') or False)
    update.update('latest', 'o/r', True, False, tmp_path / 'x.yaml')
    assert called == ['github', 'index', 'source']
