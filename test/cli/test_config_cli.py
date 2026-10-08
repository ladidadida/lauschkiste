import pytest
from typer.testing import CliRunner

import lauschkiste.cfghandler
import lauschkiste.paths
from lauschkiste_cli.cli import ctl as app

runner = CliRunner()


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.delenv(lauschkiste.paths.env_name('CONF'), raising=False)
    monkeypatch.setenv(lauschkiste.paths.HOME_ENV, str(tmp_path))
    lauschkiste.paths.set_home(None)
    yield tmp_path
    lauschkiste.paths.set_home(None)


def test_set_and_get(home):
    result = runner.invoke(app, ['config', 'set', 'library.path', '/srv/books'])
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ['config', 'get', 'library.path'])
    assert result.output.strip() == '/srv/books'
    assert (home / 'settings' / 'lauschkiste.yaml').read_text().count('#') > 0


def test_values_are_yaml(home):
    runner.invoke(app, ['config', 'set', 'library.watch', 'false'])
    assert runner.invoke(app, ['config', 'get', 'library.watch']).output.strip() == 'false'


def test_unknown_key_fails(home):
    result = runner.invoke(app, ['config', 'get', 'no.such.key'])
    assert result.exit_code == 1


def test_section_is_not_overwritten(home):
    result = runner.invoke(app, ['config', 'set', 'library', 'x'])
    assert result.exit_code == 1
    assert 'section' in result.output


def test_secrets_go_to_their_own_file_and_are_hidden(home):
    result = runner.invoke(app, ['config', 'set', 'plugins.demo.api_key', '--secret'], input='s3cret\n')
    assert result.exit_code == 0, result.output
    assert 's3cret' not in result.output
    secrets = home / 'settings' / 'secrets.yaml'
    assert 's3cret' in secrets.read_text() and oct(secrets.stat().st_mode & 0o777) == '0o600'
    assert 's3cret' not in (home / 'settings' / 'lauschkiste.yaml').read_text()

    assert runner.invoke(app, ['config', 'get', 'plugins.demo.api_key']).output.strip() == '(secret, set)'
    assert runner.invoke(app, ['config', 'get', 'plugins.demo.api_key', '--reveal']).output.strip() == 's3cret'
